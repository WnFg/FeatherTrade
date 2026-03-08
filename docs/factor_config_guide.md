# 因子配置驱动扩展指南

本文档详细说明如何使用配置驱动方式扩展因子系统，包括 `FactorConfig`、`DataSourceConfig`、`ScheduleConfig` 的完整用法。

## 1. 概述

配置驱动扩展是推荐的因子注册方式，具有以下优势：
- **轻量级** — 无需修改框架代码，只需添加配置文件或 Python 模块
- **声明式** — 配置即文档，易于理解和维护
- **自动发现** — 放入 `extensions/` 目录后自动加载，无需手动注册
- **解耦** — 用户代码与框架代码完全分离

**重要说明**：
- **因子计算逻辑（`BaseFactorLogic` 子类）必须用 Python 代码定义** — 这是因子的核心，无法用配置文件表达
- **因子元数据（`FactorConfig`）可以用配置定义** — 描述因子的名称、分类、参数等
- **数据源和调度任务可以用配置定义** — 无需编写注册代码

## 2. 配置数据结构

### 2.1 FactorConfig

定义因子的元数据，对应 `factor_definitions` 表。**注意：这只是元数据，计算逻辑仍需用代码定义。**

```python
@dataclass
class FactorConfig:
    name: str                           # 因子唯一标识（必填，必须与 BaseFactorLogic 子类名小写一致）
    category: str                       # 分类（如 Value, Momentum）
    display_name: Optional[str] = None  # 显示名称
    formula_config: Dict[str, Any] = field(default_factory=dict)  # 计算参数
    version: str = "1.0.0"              # 版本号
    description: Optional[str] = None   # 描述
```

**示例**：
```python
# 1. 先定义计算逻辑（必须用代码）
class PERatioFactor(BaseFactorLogic):
    def compute(self, data):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]

# 2. 再定义元数据配置
FactorConfig(
    name="peratioFactor",  # 必须与类名小写一致
    category="Value",
    display_name="市盈率",
    formula_config={"field": "pe"},
    description="股票市盈率指标"
)
```

### 2.2 DataSourceConfig

定义数据源实例，包括类路径、参数、时间范围和转换规则。

```python
@dataclass
class DataSourceConfig:
    name: str                           # 数据源实例名称（必填）
    source_class: str                   # 数据源类名（必填）
    params: Dict[str, Any] = field(default_factory=dict)  # 初始化参数
    time_range: Optional[Dict[str, str]] = None           # 时间范围（start/end）
    transformation: Optional[Dict[str, Any]] = None       # 列转换规则
```

**参数说明**：
- `source_class` — 可以是简单类名（如 `TuShareDataSource`）或完整路径
- `params` — 传递给 `BaseDataSource.configure()` 的参数字典
  - `symbols` — 股票代码列表（调度时会展开为多次调用）
  - 其他参数根据具体数据源类定义
- `time_range` — 支持相对时间表达式（见 2.4 节）
- `transformation` — 列重命名和类型转换规则（见 2.5 节）

**示例**：
```python
DataSourceConfig(
    name="tushare_daily_basic",
    source_class="TuShareDataSource",
    params={
        "api": "daily_basic",
        "symbols": ["000001.SZ", "600000.SH"],
        "fields": ["pe", "pb", "ps"]
    },
    time_range={"start": "today-7d", "end": "today"},
    transformation={
        "rename": {"ts_code": "symbol", "trade_date": "timestamp"},
        "type_casting": {"pe": "float", "pb": "float"}
    }
)
```

### 2.3 ScheduleConfig

定义调度任务，关联因子和数据源。

```python
@dataclass
class ScheduleConfig:
    name: str                           # 任务名称（必填）
    factor: str                         # 因子名称（必填）
    data_source: str                    # 数据源名称（必填）
    trigger: Dict[str, Any] = field(default_factory=dict)  # 触发器配置
    is_active: bool = True              # 是否激活
```

**触发器类型**：
- `cron` — 定时任务
  ```python
  trigger={"type": "cron", "expr": "0 18 * * 1-5"}  # 工作日 18:00
  ```
- `interval` — 间隔任务
  ```python
  trigger={"type": "interval", "seconds": 3600}  # 每小时
  ```
- `one-off` — 一次性任务
  ```python
  trigger={"type": "one-off", "run_time": "2024-03-15T18:00:00"}
  ```

**示例**：
```python
ScheduleConfig(
    name="daily_value_factors",
    factor="pe_ratio",
    data_source="tushare_daily_basic",
    trigger={"type": "cron", "expr": "0 18 * * 1-5"},
    is_active=True
)
```

### 2.4 相对时间范围

`DataSourceConfig.time_range` 支持以下表达式：

| 表达式 | 含义 | 示例 |
|--------|------|------|
| `today` | 当天 00:00:00 | `2024-03-15 00:00:00` |
| `today-Nd` | N 天前 | `today-3d` → 3 天前 |
| `today-Nw` | N 周前 | `today-1w` → 1 周前 |
| ISO 8601 | 固定日期 | `2024-01-01` 或 `2024-01-01T10:00:00` |

**解析时机**：调度任务执行时动态解析，确保每次执行都使用最新的相对时间。

**示例**：
```python
time_range={"start": "today-7d", "end": "today"}  # 最近 7 天
time_range={"start": "2024-01-01", "end": "today"}  # 年初至今
```

### 2.5 数据转换规则

`DataSourceConfig.transformation` 支持列重命名和类型转换：

```python
transformation={
    "rename": {
        "ts_code": "symbol",      # TuShare 的 ts_code 列重命名为 symbol
        "trade_date": "timestamp"  # trade_date 列重命名为 timestamp
    },
    "type_casting": {
        "pe": "float",
        "pb": "float",
        "volume": "int"
    }
}
```

## 3. Python 配置方式

### 3.1 创建扩展文件

在 `src/trading_system/factors/extensions/` 目录下创建 `.py` 文件，定义模块级变量：

```python
# extensions/my_value_factors.py
from src.trading_system.factors.base import BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig

# 定义因子计算逻辑（必须用代码定义）
class PERatioFactor(BaseFactorLogic):
    def compute(self, data):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]  # 取最新值

class PBRatioFactor(BaseFactorLogic):
    def compute(self, data):
        if 'pb' not in data.columns or data.empty:
            return None
        return data['pb'].iloc[-1]

# 配置因子元数据
FACTOR_CONFIGS = [
    FactorConfig(
        name="peratioFactor",  # 必须与类名小写一致
        category="Value",
        display_name="市盈率",
        formula_config={"field": "pe"}
    ),
    FactorConfig(
        name="pbratiofactor",  # 必须与类名小写一致
        category="Value",
        display_name="市净率",
        formula_config={"field": "pb"}
    )
]

# 配置数据源
DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_daily_basic",
        source_class="TuShareDataSource",
        params={
            "api": "daily_basic",
            "symbols": ["000001.SZ", "600000.SH", "000002.SZ"],
            "fields": ["pe", "pb", "ps", "total_mv"]
        },
        time_range={"start": "today-3d", "end": "today"},
        transformation={
            "rename": {"ts_code": "symbol", "trade_date": "timestamp"}
        }
    )
]

# 配置调度任务
SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_job",
        factor="peratioFactor",  # 必须与 FactorConfig.name 一致
        data_source="tushare_daily_basic",
        trigger={"type": "cron", "expr": "0 18 * * 1-5"}
    ),
    ScheduleConfig(
        name="daily_pb_job",
        factor="pbratiofactor",
        data_source="tushare_daily_basic",
        trigger={"type": "cron", "expr": "5 18 * * 1-5"}
    )
]
```

### 3.2 自动发现

`FactorService` 初始化时会自动：
1. 扫描 `extensions/` 目录下的所有 `.py` 文件
2. 导入模块并查找 `FACTOR_CONFIGS`、`DATA_SOURCE_CONFIGS`、`SCHEDULE_CONFIGS` 变量
3. 注册所有配置到 `FactorRegistry`
4. 发现 `BaseFactorLogic` 和 `BaseDataSource` 子类

无需手动调用任何注册方法。

## 4. YAML 配置方式

### 4.1 创建 YAML 文件

**重要限制**：YAML 文件只能定义配置（元数据、数据源、调度），**不能定义计算逻辑**。

如果使用 YAML 配置因子，必须配合 Python 文件定义 `BaseFactorLogic` 子类。

在 `src/trading_system/factors/extensions/` 目录下创建 `.yaml` 文件：

```yaml
# extensions/my_value_factors.yaml
factor_configs:
  - name: peratioFactor  # 必须与 Python 文件中的类名小写一致
    category: Value
    display_name: 市盈率
    formula_config:
      field: pe
    description: 股票市盈率指标

  - name: pbratiofactor
    category: Value
    display_name: 市净率
    formula_config:
      field: pb

data_source_configs:
  - name: tushare_daily_basic
    source_class: TuShareDataSource
    params:
      api: daily_basic
      symbols:
        - "000001.SZ"
        - "600000.SH"
      fields:
        - pe
        - pb
    time_range:
      start: today-3d
      end: today
    transformation:
      rename:
        ts_code: symbol
        trade_date: timestamp

schedule_configs:
  - name: daily_pe_job
    factor: peratioFactor
    data_source: tushare_daily_basic
    trigger:
      type: cron
      expr: "0 18 * * 1-5"
    is_active: true
```

**配合的 Python 文件**（定义计算逻辑）：
```python
# extensions/my_value_factors_logic.py
from src.trading_system.factors.base import BaseFactorLogic

class PERatioFactor(BaseFactorLogic):
    def compute(self, data):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]

class PBRatioFactor(BaseFactorLogic):
    def compute(self, data):
        if 'pb' not in data.columns or data.empty:
            return None
        return data['pb'].iloc[-1]
```

### 4.2 注意事项

- **YAML 文件只能定义配置，不能定义计算逻辑类**
- **必须配合 Python 文件定义 `BaseFactorLogic` 子类**
- 或者使用内置的通用因子逻辑（如 `MovingAverageFactor`）
- 推荐做法：将计算逻辑和配置放在同一个 Python 文件中，避免分散

## 5. 完整示例：TuShare PE/PB 定时抓取

### 5.1 需求描述

通过 TuShare 数据源获取公司的价值因子（PE、PB），执行策略是每天 18:00 定时抽取。

### 5.2 实现步骤

**步骤 1：设置 TuShare Token**

```bash
export TUSHARE_TOKEN="your_token_here"
```

**步骤 2：创建扩展文件**

```python
# extensions/tushare_value_factors.py
from src.trading_system.factors.base import BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig

class PEFactor(BaseFactorLogic):
    """市盈率因子"""
    def compute(self, data):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]  # 取最新值

class PBFactor(BaseFactorLogic):
    """市净率因子"""
    def compute(self, data):
        if 'pb' not in data.columns or data.empty:
            return None
        return data['pb'].iloc[-1]

# 因子定义
FACTOR_CONFIGS = [
    FactorConfig(
        name="pefactor",  # 必须与类名小写一致
        category="Value",
        display_name="市盈率",
        description="从 TuShare daily_basic 获取的市盈率"
    ),
    FactorConfig(
        name="pbfactor",
        category="Value",
        display_name="市净率",
        description="从 TuShare daily_basic 获取的市净率"
    )
]

# 数据源配置
DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_value_source",
        source_class="TuShareDataSource",
        params={
            "api": "daily_basic",
            "symbols": [
                "000001.SZ",  # 平安银行
                "600000.SH",  # 浦发银行
                "000002.SZ"   # 万科A
            ],
            "fields": ["ts_code", "trade_date", "pe", "pb", "ps", "total_mv"]
        },
        time_range={
            "start": "today-3d",  # 最近 3 天
            "end": "today"
        },
        transformation={
            "rename": {
                "ts_code": "symbol",
                "trade_date": "timestamp"
            },
            "type_casting": {
                "pe": "float",
                "pb": "float"
            }
        }
    )
]

# 调度任务配置
SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_extraction",
        factor="pefactor",
        data_source="tushare_value_source",
        trigger={
            "type": "cron",
            "expr": "0 18 * * 1-5"  # 工作日 18:00
        },
        is_active=True
    ),
    ScheduleConfig(
        name="daily_pb_extraction",
        factor="pbfactor",
        data_source="tushare_value_source",
        trigger={
            "type": "cron",
            "expr": "5 18 * * 1-5"  # 工作日 18:05（错开 5 分钟）
        },
        is_active=True
    )
]
```

**步骤 3：启动服务**

```python
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.scheduler import TaskScheduler

# 初始化服务（自动发现扩展）
service = FactorService(db_path="factors.db")

# 启动调度器
scheduler = TaskScheduler(service)
scheduler.load_all_config_tasks()  # 加载所有 ScheduleConfig 任务
scheduler.start()

# 保持运行
import time
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    scheduler.stop()
```

**步骤 4：验证结果**

```python
# 查询因子值
values = service.get_factor_values("000001.SZ", "pefactor", limit=10)
for v in values:
    print(f"{v.timestamp}: {v.value}")
```

### 5.3 执行流程

1. **18:00 触发** — APScheduler 触发 `daily_pe_extraction` 任务
2. **读取配置** — 从 `ScheduleConfig` 读取 factor 和 data_source
3. **解析时间** — `TimeRangeResolver` 将 `today-3d` 解析为具体日期
4. **展开 symbols** — 从 `DataSourceConfig.params.symbols` 提取 `["000001.SZ", "600000.SH", "000002.SZ"]`
5. **逐个计算** — 对每个 symbol 调用 `compute_and_store()`：
   - 实例化 `TuShareDataSource`，调用 `configure(params)`
   - 调用 `fetch_data(symbol, start, end)` 获取数据
   - 应用 `transformation` 规则（列重命名、类型转换）
   - 实例化 `PEFactor`，调用 `compute(data)`
   - 将结果写入 `factor_values` 表
6. **记录日志** — 写入 `task_execution_logs` 表

## 6. 最佳实践

### 6.1 命名约定

- **因子名称** — 使用 snake_case，与 `BaseFactorLogic` 子类名小写一致
- **数据源名称** — 描述性名称，如 `tushare_daily_basic`、`csv_price_data`
- **任务名称** — 描述性名称，如 `daily_value_factors`、`hourly_momentum_update`

### 6.2 时间范围选择

- **历史回测** — 使用固定日期 `{"start": "2023-01-01", "end": "2023-12-31"}`
- **滚动窗口** — 使用相对时间 `{"start": "today-30d", "end": "today"}`
- **增量更新** — 使用 `{"start": "today-1d", "end": "today"}`

### 6.3 调度时间避让

- 避免所有任务在整点执行（如 `0 * * * *`）
- 错开任务执行时间，避免资源竞争
- TuShare 有 API 限流，建议间隔 5 分钟以上

### 6.4 错误处理

- `BaseDataSource.fetch_data()` 返回空 DataFrame 时，`compute()` 应返回 `None`
- `FactorService` 会跳过 `None` 值，不写入数据库
- 调度任务失败会记录到 `task_execution_logs` 表

## 7. 常见问题

### Q1: 如何调试配置是否被正确加载？

```python
service = FactorService(db_path="factors.db")

# 检查因子定义
factor_def = service.db.get_factor_definition("pe_ratio")
print(factor_def)

# 检查数据源配置
ds_config = service.registry.get_data_source_config("tushare_daily_basic")
print(ds_config)

# 检查调度配置
schedule_config = service.registry.get_schedule_config("daily_value_factors")
print(schedule_config)
```

### Q2: 如何手动触发调度任务？

```python
# 方式 1：直接调用 compute_and_store
service.compute_and_store(
    symbol="000001.SZ",
    factor_name="pe_ratio",
    data_source_name="tushare_daily_basic",
    start_time=datetime(2024, 3, 1),
    end_time=datetime(2024, 3, 15)
)

# 方式 2：通过调度器立即执行
scheduler.scheduler.get_job("daily_pe_extraction").modify(next_run_time=datetime.now())
```

### Q3: 如何更新已有配置？

- **Python 配置** — 直接修改 `.py` 文件，重启服务
- **YAML 配置** — 修改 `.yaml` 文件，重启服务
- **数据库配置** — `FactorConfig` 会自动 upsert 到 `factor_definitions` 表

### Q4: 如何禁用某个调度任务？

```python
# 方式 1：修改配置文件
ScheduleConfig(
    name="daily_value_factors",
    factor="pe_ratio",
    data_source="tushare_daily_basic",
    trigger={"type": "cron", "expr": "0 18 * * 1-5"},
    is_active=False  # 设置为 False
)

# 方式 2：运行时暂停
scheduler.scheduler.pause_job("daily_value_factors")
```

## 8. 参考资料

- `src/trading_system/factors/config.py` — 配置数据结构定义
- `src/trading_system/factors/time_resolver.py` — 时间范围解析器
- `src/trading_system/factors/registry.py` — 配置扫描和注册逻辑
- `src/trading_system/factors/scheduler.py` — 调度任务执行逻辑
- `src/trading_system/factors/extensions/example_value_factors.py` — 完整示例
