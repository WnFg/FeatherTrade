# 文档目录

本目录包含 TradeSystem 框架的完整使用说明。

---

## 快速导航

### 入门

| 文档 | 说明 |
|---|---|
| [架构概览](architecture.md) | 事件驱动架构、模块职责、事件流 |
| [设计目标](goals.md) | 框架设计原则与非目标 |

### 策略开发与回测

| 文档 | 说明 |
|---|---|
| [策略机制](策略机制.md) | 策略基类接口、`on_bar` / `on_tick`、信号发送、`StatefulStrategy` 状态机与风控钩子 |
| [扩展指南](extension-guide.md) | 如何扩展策略、数据适配器、执行适配器 |

### 因子管理

| 文档 | 说明 |
|---|---|
| [因子模型](factor_model.md) | 因子系统架构：fetch → transform → compute → store |
| [因子快捷注册](因子快捷注册.md) | `QuickRegisterConfig` 一键批量注册因子，无需逐个定义 |
| [用户注册数据源与因子用例](用户注册数据源与因子用例.md) | 注册自定义数据源、因子定义、调度任务的完整示例 |
| [TuShare 数据源](tuShare数据源.md) | `TuShareDataSource` 配置与使用，A 股日线行情 / 每日指标接口说明 |
| [可扩展性与调度](factor_extensibility_scheduling.md) | extensions/ 目录扩展机制、APScheduler 定时任务配置 |
| [因子配置指南](factor_config_guide.md) | `FactorConfig` / `DataSourceConfig` / `ScheduleConfig` 数据类参数说明 |

---

## 阅读路径建议

### 初次使用者

1. 阅读 [架构概览](architecture.md) 了解整体设计
2. 阅读 [策略机制](策略机制.md) 学习如何编写策略
3. 参考 `run_backtest.py` / `run_factor_backtest.py` 运行第一个回测

### 想接入外部数据的用户

1. 阅读 [TuShare 数据源](tuShare数据源.md) 了解内置数据源
2. 阅读 [因子快捷注册](因子快捷注册.md) 一键拉取并注册因子
3. 参考 `src/trading_system/factors/extensions/tushare_daily_task.py` 复制并修改 `SYMBOLS`

### 高阶用户 / 框架扩展者

1. 阅读 [可扩展性与调度](factor_extensibility_scheduling.md) 了解 `extensions/` 自动发现机制
2. 阅读 [用户注册数据源与因子用例](用户注册数据源与因子用例.md) 掌握完整扩展流程
3. 阅读 [扩展指南](extension-guide.md) 了解策略和适配器的扩展接口
4. 参考 `src/trading_system/factors/base.py` 中的 `BaseFactorLogic` / `BaseDataSource` 接口实现自定义组件

---

## 示例脚本

| 脚本 | 说明 |
|---|---|
| `run_backtest.py` | 基于 CSV 数据的 MA 交叉策略回测 |
| `run_risk_backtest.py` | 带固定止损 / 止盈风控的回测 |
| `run_factor_backtest.py` | 基于因子数据库的双均线趋势策略回测（000001.SZ） |
| `src/trading_system/factors/extensions/tushare_daily_task.py` | 拉取 A 股日线行情并注册为因子 |
| `src/trading_system/factors/extensions/tushare_basic_task.py` | 拉取每日指标并注册为因子 |
| `src/trading_system/factors/extensions/tushare_daily_task_X.py` | 用户自定义股票日线行情任务模板 |
| `src/trading_system/factors/extensions/tushare_basic_task_Y.py` | 用户自定义股票每日指标任务模板 |
