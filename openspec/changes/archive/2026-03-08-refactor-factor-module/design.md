## Context

当前 `factors/` 模块已有基本骨架（`DiscoveryEngine`、`FactorRegistry`、`DataSourceFactory`、`TaskScheduler`），但存在以下核心问题：

1. **数据源实例化强依赖数据库**：用户必须先向 DB 写入 `data_source_instances` 记录才能运行，无法用代码或配置文件直接描述"从 TuShare 抓取腾讯近三天日线"这样的意图。
2. **调度任务的 symbol / 时间范围硬编码**：`_execute_task_wrapper` 中 `symbol` 和时间窗口是 TODO 占位，无法从任务配置中动态解析。
3. **因子定义仍需手动调用 API 写库**：没有声明式的注册入口，用户必须了解 `FactorDefinition` 数据模型。
4. **框架与用户代码边界模糊**：`extensions/` 目录存在但没有标准化的配置文件格式，用户不知道如何声明一个完整的"因子包"。

本次重构在现有骨架基础上补全缺失的轻量级配置层，不推倒重来。

## Goals / Non-Goals

**Goals:**
- 用户可通过 Python dataclass 或 YAML 文件声明因子定义、数据源实例、调度任务，无需直接操作数据库
- 数据源实例支持相对时间表达式（如 `today-3d ~ today`）和多 symbol 列表
- 调度任务执行时能从配置中正确解析 symbol 列表和动态时间窗口
- 框架核心代码（`builtin/`）与用户扩展代码（`extensions/`）目录职责清晰
- 因子计算结果写入 SQLite `factor_values` 表，行为不变

**Non-Goals:**
- 不引入新的持久化后端（Redis、PostgreSQL 等）
- 不实现 Web UI 或 REST API
- 不支持分布式调度
- 不修改 `factor_values` 表结构

## Decisions

### D1：轻量级配置格式 — Python dataclass 优先，YAML 作为无代码选项

**选择**：定义 `FactorConfig`、`DataSourceConfig`、`ScheduleConfig` 三个 dataclass，用户在 `extensions/` 下的任意 `.py` 文件中实例化并赋值给模块级变量 `FACTOR_CONFIGS`、`DATA_SOURCE_CONFIGS`、`SCHEDULE_CONFIGS`。同时支持同名 `.yaml` 文件作为等价的无代码声明方式。

**重要限制**：`FactorConfig` 只是因子的元数据配置（名称、分类、参数等），**因子的计算逻辑（`BaseFactorLogic` 子类）必须用 Python 代码定义**。这是因子的核心部分，无法用配置文件表达。

**为什么不用纯 YAML**：Python dataclass 有类型提示和 IDE 补全，对开发者更友好；YAML 适合运维/非开发者场景，但只能定义元数据和配置，不能定义计算逻辑。

**为什么不用数据库作为主要注册入口**：数据库适合运行时状态，不适合版本控制下的配置声明。配置文件可以 git 管理，数据库记录是派生产物。

```python
# extensions/my_factors.py 示例
from trading_system.factors.base import BaseFactorLogic
from trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig

# 1. 定义计算逻辑（必须用代码）
class PERatioFactor(BaseFactorLogic):
    def compute(self, data, config):
        if 'pe' not in data.columns or data.empty:
            return pd.DataFrame()
        result = pd.DataFrame({
            'timestamp': [data['timestamp'].iloc[-1]],
            'symbol': [data['symbol'].iloc[0]],
            'value': [data['pe'].iloc[-1]]
        })
        return result

# 2. 定义元数据配置
FACTOR_CONFIGS = [
    FactorConfig(
        name="peratioFactor",  # 必须与类名小写一致
        category="Value",
        formula_config={"field": "pe"}
    ),
]

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_daily_basic",
        source_class="TuShareDataSource",
        params={"api": "daily_basic", "symbols": ["000001.SZ", "600000.SH"]},
        time_range={"start": "today-3d", "end": "today"},
        transformation={"rename": {"ts_code": "symbol", "trade_date": "timestamp"}},
    ),
]

SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_job",
        factor="peratioFactor",
        data_source="tushare_daily_basic",
        trigger={"type": "cron", "expr": "0 18 * * 1-5"},
    ),
]
```

### D2：时间范围动态表达式 — 简单 DSL，执行时求值

**选择**：`time_range` 字段支持字符串表达式，格式为 `today[-Nd]`，由 `TimeRangeResolver` 在任务执行时解析为具体 `datetime`。

**备选方案**：存储固定日期 → 不适合定期任务；引入 Jinja2 模板 → 过重。

**规则**：
- `today` → 当天 00:00:00
- `today-3d` → 3 天前 00:00:00
- `today-1w` → 7 天前
- 也接受 ISO 8601 字符串作为固定日期

### D3：多 symbol 支持 — DataSourceConfig 持有 symbol 列表，调度时展开

**选择**：`DataSourceConfig.params.symbols` 为列表，`TaskScheduler` 执行时对每个 symbol 调用一次 `compute_and_store`。

**为什么不在 DataSource 内部处理多 symbol**：`BaseDataSource.fetch_data(symbol, ...)` 接口已固定，保持单 symbol 语义更简单，批量由调度层展开。

### D4：配置加载时机 — DiscoveryEngine 启动时扫描，DB 作为缓存/持久化

**选择**：`FactorService.__init__` 时，`DiscoveryEngine` 扫描 `extensions/` 目录，收集所有 `*_CONFIGS` 变量和 YAML 文件，合并后：
1. 将 `FactorConfig` upsert 到 `factor_definitions` 表（幂等）
2. 将 `DataSourceConfig` 保存到内存 `_ds_config_map`（不强制写 DB，除非用户显式持久化）
3. 将 `ScheduleConfig` 注册到 APScheduler（任务 ID 由 name 决定，重启后 SQLAlchemy jobstore 自动恢复）

**为什么 DataSourceConfig 不强制写 DB**：数据源配置是声明式的，每次启动重新加载即可；只有需要跨进程共享或动态修改时才持久化。

### D5：`BaseDataSource` 接口扩展 — 增加无参构造 + `configure()` 方法

**选择**：`BaseDataSource` 新增可选的 `configure(params: dict)` 方法，`DataSourceFactory` 在实例化后调用它传入参数，而不是通过构造函数。这样 `DiscoveryEngine` 可以用无参构造发现类，再由 Factory 注入配置。

**向后兼容**：`configure()` 默认实现为空，现有子类无需修改。

### D6：调度器与服务的配合 — 两种驱动模式，统一执行流程

**选择**：`TaskScheduler` 支持两种任务驱动模式：
1. **配置驱动**（`ScheduleConfig`）：从 registry 读取配置 → 解析时间范围 → 展开 symbols → 逐个调用 `compute_and_store()`
2. **DB 驱动**（`ScheduledTask`）：从 DB 读取任务 → 解析时间范围 → 展开 symbols → 逐个调用 `compute_and_store()` → 记录执行日志

**执行流程**：
- 配置驱动：`_execute_config_task_wrapper` → 获取 `ScheduleConfig` 和 `DataSourceConfig` → 提取 `params.symbols` → 使用 `TimeRangeResolver` 解析 `time_range` → 对每个 symbol 调用 `FactorService.compute_and_store()`
- DB 驱动：`_execute_task_wrapper` → 获取 `ScheduledTask` 和 `DataSourceInstance` → 提取 `parameters.symbols` 或 `parameters.symbol` → 解析 `parameters.time_range` → 对每个 symbol 调用 `compute_and_store()` → 写入 `task_execution_logs`

**数据源解析优先级**（`FactorService._get_source`）：
1. `DataSourceConfig` from registry（配置驱动）
2. `DataSourceInstance` from DB（DB 驱动）
3. Dynamic class registry（fallback）

**实例化策略**（`FactorService._instantiate_from_config`）：
1. 优先从 `registry.get_source_class()` 查找类（支持扩展中的简单类名如 `MockDataSource`）
2. Fallback 到 `DataSourceFactory.create_instance()`（处理 TEMPLATES 映射和完整路径）

**为什么两种模式并存**：配置驱动适合开发和版本控制，DB 驱动适合运行时动态创建任务；两者共享 `compute_and_store()` 核心逻辑，保持一致性。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|---|---|
| YAML 与 Python 配置同时存在，用户不知道用哪个 | 文档明确推荐 Python 优先；YAML 仅作为补充，不支持 lambda/callable |
| `today-3d` DSL 过于简单，无法表达"上一个交易日" | 当前版本只支持自然日偏移；交易日历支持列为 future work |
| APScheduler SQLAlchemy jobstore 与 factor DB 是两个 SQLite 文件 | 可配置为同一文件不同表，但默认分离以降低耦合 |
| 多 symbol 展开在调度层，大量 symbol 时性能差 | 当前场景（A 股个股）数量可控；批量优化列为 future work |
| `DiscoveryEngine` 扫描时执行用户代码，存在副作用风险 | 文档约束：`*_CONFIGS` 变量只能是纯数据声明，不能有副作用 |

## Migration Plan

1. 新增 `config.py`（`FactorConfig`、`DataSourceConfig`、`ScheduleConfig` dataclass）和 `time_resolver.py`（`TimeRangeResolver`）
2. 扩展 `DiscoveryEngine` 支持扫描 `*_CONFIGS` 变量和 `.yaml` 文件
3. 扩展 `BaseDataSource` 增加 `configure()` 方法（默认空实现，向后兼容）
4. 修改 `TaskScheduler._execute_task_wrapper`（DB 驱动）：从 `DataSourceInstance.parameters` 读取 symbol 列表和时间范围，使用 `TimeRangeResolver` 解析
5. 新增 `TaskScheduler._execute_config_task_wrapper`（配置驱动）：从 `ScheduleConfig` 读取关联的 `DataSourceConfig`，提取 symbols 列表，解析时间范围，逐个 symbol 调用 `compute_and_store()`
6. 修改 `TaskScheduler.add_task_from_config`：正确处理 cron、interval、one-off 三种 trigger 类型的配置提取
7. 修改 `FactorService._instantiate_from_config`：优先从 registry 查找类（支持扩展中的简单类名），再 fallback 到 DataSourceFactory
8. 修改 `FactorService.__init__`：支持接收 db_path 字符串或 FactorDatabase 实例；确保先转换 db 为实例再传给 FactorRegistry
9. 新增 `FactorDatabase.get_factor_definition_by_id()` 和 `close()` 方法
10. 更新 `builtin/data_sources.py` 中 `TuShareDataSource` 实现 `configure()`
11. 在 `extensions/` 下添加示例文件 `example_value_factors.py`（包含 `BaseFactorLogic` 子类 + 配置）
12. 更新 `tests/unit/test_factor_system.py`；新增 `tests/integration/test_config_driven_pipeline.py`
13. 更新文档：`docs/factor_model.md`、`docs/factor_config_guide.md`、`CLAUDE.md`

**回滚**：所有改动向后兼容（`configure()` 默认空实现，DB 注册路径保留），可按文件粒度回滚。

## Open Questions

- `ScheduleConfig` 是否需要支持 `symbols` 覆盖（即调度级别的 symbol 列表优先于数据源配置中的列表）？当前设计由数据源配置持有 symbol，调度配置不重复声明。**已解决**：保持当前设计，symbol 列表由 `DataSourceConfig.params.symbols` 持有。
- TuShare `daily_basic` 接口的 `fields` 参数是否需要在 `DataSourceConfig` 中可配置？**已解决**：支持通过 `params.fields` 配置，默认包含常用字段。
- 因子计算逻辑能否用配置表达？**已明确**：不能。`BaseFactorLogic.compute()` 方法是因子的核心逻辑，必须用 Python 代码定义。`FactorConfig` 只是元数据配置。
