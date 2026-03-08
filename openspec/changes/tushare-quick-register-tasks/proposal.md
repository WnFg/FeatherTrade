## Why

系统已具备因子快捷注册能力（`QuickRegisterConfig` + `ColumnExtractLogic`），但尚无面向用户的扩展示例，展示如何将 TuShare 的 A股日线行情（`daily`）和每日指标（`daily_basic`）批量注册为因子。本变更提供两个标准用户扩展任务，开箱即用。

## What Changes

- 新增扩展文件 `src/trading_system/factors/extensions/tushare_daily_task.py`：为股票 `X` 注册 TuShare `daily` 接口的全部数值因子，时间范围近一年
- 新增扩展文件 `src/trading_system/factors/extensions/tushare_basic_task.py`：为股票 `Y` 注册 TuShare `daily_basic` 接口的全部数值因子，时间范围近一年
- 两个扩展均使用 `QUICK_REGISTER_CONFIGS` + `DATA_SOURCE_CONFIGS`，由 `FactorService` 在初始化时自动发现并执行

## Capabilities

### New Capabilities

- `tushare-daily-quick-register-task`：A股日线行情快捷注册扩展任务，覆盖 open/high/low/close/pre_close/change/pct_chg/vol/amount 等字段
- `tushare-basic-quick-register-task`：每日指标快捷注册扩展任务，覆盖 close/turnover_rate/turnover_rate_f/volume_ratio/pe/pe_ttm/pb/ps/ps_ttm/dv_ratio/dv_ttm/total_share/float_share/free_share/total_mv/circ_mv 等字段

### Modified Capabilities

（无）

## Impact

- 新增文件：`src/trading_system/factors/extensions/tushare_daily_task.py`
- 新增文件：`src/trading_system/factors/extensions/tushare_basic_task.py`
- 依赖：`TuShareDataSource`（已有），`QuickRegisterConfig`（已有），`TUSHARE_TOKEN` 环境变量
- 无破坏性变更：纯新增扩展文件，不修改任何现有代码
