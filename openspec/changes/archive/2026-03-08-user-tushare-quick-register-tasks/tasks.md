## 1. 日线行情因子任务

- [x] 1.1 创建 `src/trading_system/factors/extensions/tushare_daily_task_X.py`，复用现有 `tushare_daily_task.py` 结构，`SYMBOLS=["X"]`，`DataSourceConfig.name="tushare_daily_X"`，顶部注释说明用户需修改 SYMBOLS

## 2. 每日指标因子任务

- [x] 2.1 创建 `src/trading_system/factors/extensions/tushare_basic_task_Y.py`，复用现有 `tushare_basic_task.py` 结构，`SYMBOLS=["Y"]`，`DataSourceConfig.name="tushare_basic_Y"`，顶部注释说明用户需修改 SYMBOLS
