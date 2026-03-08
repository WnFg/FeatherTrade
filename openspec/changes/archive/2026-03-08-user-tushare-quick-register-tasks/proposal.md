## Why

用户需要将指定股票代码（ts_code）近一年的 A 股日线行情（TuShare `daily` 接口）和每日指标（TuShare `daily_basic` 接口）批量拉取并快捷注册为因子，以便在回测和策略开发中直接使用。

## What Changes

- 新增 `tushare_daily_task_X.py` 扩展文件：针对用户指定的 ts_code（代号 X），通过 `QUICK_REGISTER_CONFIGS` 快捷注册 `daily_open`、`daily_high`、`daily_low`、`daily_close` 等 9 个日线行情因子，并抓取近一年数据存入因子库。
- 新增 `tushare_basic_task_Y.py` 扩展文件：针对用户指定的 ts_code（代号 Y），通过 `QUICK_REGISTER_CONFIGS` 快捷注册 `basic_pe`、`basic_pb`、`basic_turnover_rate` 等 16 个每日指标因子，并抓取近一年数据存入因子库。
- 两个文件均采用 `__main__` 可执行入口，用户只需修改文件顶部的 `SYMBOLS` 变量即可复用。

## Capabilities

### New Capabilities
- `tushare-daily-user-task`: 用户指定股票的日线行情因子快捷注册与数据拉取任务（daily 接口，前缀 `daily_`）
- `tushare-basic-user-task`: 用户指定股票的每日指标因子快捷注册与数据拉取任务（daily_basic 接口，前缀 `basic_`）

### Modified Capabilities

## Impact

- 新增 `src/trading_system/factors/extensions/tushare_daily_task_X.py`
- 新增 `src/trading_system/factors/extensions/tushare_basic_task_Y.py`
- 依赖：`TuShareDataSource`、`QuickRegisterConfig`、`FactorService`、`TimeRangeResolver`（均已存在）
- 需要 `TUSHARE_TOKEN` 环境变量或 `workspace/config/factors.yaml` 配置
