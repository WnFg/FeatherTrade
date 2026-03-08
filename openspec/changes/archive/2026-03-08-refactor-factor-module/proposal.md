## Why

当前因子管理模块的扩展性不足：用户注册新因子、数据源和调度任务需要直接修改框架代码，框架逻辑与用户逻辑高度耦合。本次重构旨在通过插件式扩展机制和轻量级配置手段，让用户无需触碰框架内部即可完整地完成「注册因子→配置数据源→设定调度」全流程。

## What Changes

- **BREAKING** 重构 `factors/` 模块目录结构，将框架核心代码与用户扩展代码彻底分离（`builtin/` vs `extensions/`）
- 引入基于 Python 文件 / YAML 配置的因子元数据注册机制，替代现有的数据库直接注册方式（**注意**：因子计算逻辑 `BaseFactorLogic` 子类仍需用 Python 代码定义，配置只能表达元数据）
- 引入 `DiscoveryEngine`：自动扫描 `extensions/` 目录，发现并注册 `BaseFactorLogic` 和 `BaseDataSource` 子类，无需手动调用注册 API
- 引入 `DataSourceFactory`：支持通过 class path 字符串 + 参数字典动态实例化数据源；用户可用轻量级代码（Python dict/dataclass）或 YAML 配置文件描述抓取策略（如数据源类型、股票列表、相对时间范围等），实例配置可选持久化到数据库
- 引入 `ParameterTransformer`：支持列重命名、类型转换等用户自定义转换规则，配置随数据源实例存储
- 引入 `TaskScheduler`：封装 APScheduler，支持 cron / interval / 一次性三种调度类型，任务持久化到 SQLite；支持配置驱动（`ScheduleConfig`）和 DB 驱动（`ScheduledTask`）两种模式
- 因子计算结果仍写入 SQLite `factor_values` 表，行为不变
- 新增内置 `TuShareDataSource`，支持通过环境变量 `TUSHARE_TOKEN` 接入 TuShare 数据

## Capabilities

### New Capabilities
- `factor-extensibility`: 基于 `extensions/` 目录的自动发现与注册机制，用户通过继承 `BaseFactorLogic` / `BaseDataSource` 并放置文件即可完成扩展；因子计算逻辑必须用 Python 代码定义，元数据可通过 `FactorConfig` 配置
- `factor-data-source-instantiation`: 数据源模板 + 实例化机制，用户可通过轻量级代码（Python dict/dataclass）或 YAML 配置文件描述抓取策略（数据源类型、股票列表、时间范围等动态表达式），框架自动实例化为可执行数据源；实例化时优先从 registry 查找已发现的类，再 fallback 到 DataSourceFactory 的 TEMPLATES 映射
- `factor-scheduling`: 调度引擎，支持 cron 定时、interval 间隔、一次性三种触发方式；支持配置驱动（`ScheduleConfig`）和 DB 驱动（`ScheduledTask`）两种模式；配置驱动模式下自动展开多 symbol 列表并解析相对时间范围
- `tushare-integration`: 内置 TuShare 数据源，支持日线行情（`daily`）和每日指标（`daily_basic`）接口，用于获取 PE/PB 等价值因子原始数据

### Modified Capabilities
- `factor-registry`: 注册方式从纯数据库 API 扩展为支持代码/配置文件自动发现；DiscoveryEngine 成为主要注册入口，数据库持久化作为补充；因子计算逻辑（`BaseFactorLogic` 子类）必须用代码定义，元数据可通过 `FactorConfig` 配置
- `customizable-ingestion`: `FactorService.compute_and_store` 新增接受数据源实例 ID 或配置名称的入参，并在 fetch 后自动应用 `ParameterTransformer`；数据源解析优先级：(1) DataSourceConfig from registry → (2) DataSourceInstance from DB → (3) dynamic class registry

## Impact

- **代码**: `src/trading_system/factors/` 全模块重构；新增 `registry.py`、`factory.py`、`transformer.py`、`scheduler.py`、`base.py`；`builtin/` 下新增 `factors.py`、`data_sources.py`
- **数据库**: 新增 `data_source_instances`、`scheduled_tasks`、`task_execution_logs` 三张表；`factor_definitions` 已有表结构保持兼容
- **依赖**: 新增 `apscheduler`；TuShare 集成需 `tushare` 包及 `TUSHARE_TOKEN` 环境变量（可选）
- **测试**: 现有 `tests/unit/test_factor_system.py` 需适配新 API；新增集成测试覆盖扩展发现、数据源实例化、调度执行全流程
