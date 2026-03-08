## 1. A股日线行情扩展任务

- [x] 1.1 创建 `src/trading_system/factors/extensions/tushare_daily_task.py`，定义 `DATA_SOURCE_CONFIGS`：名称 `"tushare_daily_X"`，`source_class="TuShareDataSource"`，`api="daily"`，`symbols=["X"]`，`time_range={"start": "today-365d", "end": "today"}`
- [x] 1.2 在同文件定义 `QUICK_REGISTER_CONFIGS`：`data_source="tushare_daily_X"`，`fields=["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]`，`prefix="daily_"`，`category="TuShareDaily"`

## 2. 每日指标扩展任务

- [x] 2.1 创建 `src/trading_system/factors/extensions/tushare_basic_task.py`，定义 `DATA_SOURCE_CONFIGS`：名称 `"tushare_basic_Y"`，`source_class="TuShareDataSource"`，`api="daily_basic"`，`symbols=["Y"]`，`time_range={"start": "today-365d", "end": "today"}`
- [x] 2.2 在同文件定义 `QUICK_REGISTER_CONFIGS`：`data_source="tushare_basic_Y"`，`fields=["close", "turnover_rate", "turnover_rate_f", "volume_ratio", "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm", "total_share", "float_share", "free_share", "total_mv", "circ_mv"]`，`prefix="basic_"`，`category="TuShareBasic"`

## 3. 验证

- [x] 3.1 确认两个文件可被 `DiscoveryEngine` 正确导入（无语法错误，`import` 路径正确）
- [x] 3.2 确认 `FactorService` 初始化后，`daily_close`、`basic_pe` 等因子定义可通过 `get_factor_definition` 查询（需 TuShare token 可用时手动验证，或通过 mock 测试）
