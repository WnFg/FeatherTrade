## ADDED Requirements

### Requirement: TuShare Daily Basic Data Source Config (User Symbol)
The extension SHALL define a `DataSourceConfig` named `"tushare_basic_Y"` that uses `TuShareDataSource` with `api="daily_basic"` and `symbols=["Y"]`（Y 为用户指定的 ts_code），covering a time range of approximately one year ending today.

#### Scenario: Data source config present
- **WHEN** `FactorService` initializes with this extension in the extensions directory
- **THEN** `service.registry.get_data_source_config("tushare_basic_Y")` SHALL return the config

---

### Requirement: TuShare Daily Basic Quick Register (User Symbol)
The extension SHALL define a `QUICK_REGISTER_CONFIGS` entry with `data_source="tushare_basic_Y"` and `fields=["close", "turnover_rate", "turnover_rate_f", "volume_ratio", "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm", "total_share", "float_share", "free_share", "total_mv", "circ_mv"]`, using `prefix="basic_"` and `category="TuShareBasic"`.

#### Scenario: Factors auto-registered and data ingested
- **WHEN** the user executes `python -m src.trading_system.factors.extensions.tushare_basic_task_Y`
- **THEN** factor definitions for all prefixed fields (e.g. `basic_close`, `basic_pe`, `basic_pb`) SHALL exist in the database, and factor values for symbol Y SHALL be stored

#### Scenario: User can customize symbol
- **WHEN** the user modifies the `SYMBOLS` variable at the top of the extension file
- **THEN** the task SHALL fetch and register data for the updated symbol(s)
