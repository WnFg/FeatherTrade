## ADDED Requirements

### Requirement: TuShare Daily Data Source Config (User Symbol)
The extension SHALL define a `DataSourceConfig` named `"tushare_daily_X"` that uses `TuShareDataSource` with `api="daily"` and `symbols=["X"]`（X 为用户指定的 ts_code），covering a time range of approximately one year ending today.

#### Scenario: Data source config present
- **WHEN** `FactorService` initializes with this extension in the extensions directory
- **THEN** `service.registry.get_data_source_config("tushare_daily_X")` SHALL return the config

---

### Requirement: TuShare Daily Quick Register (User Symbol)
The extension SHALL define a `QUICK_REGISTER_CONFIGS` entry with `data_source="tushare_daily_X"` and `fields=["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]`, using `prefix="daily_"` and `category="TuShareDaily"`.

#### Scenario: Factors auto-registered and data ingested
- **WHEN** the user executes `python -m src.trading_system.factors.extensions.tushare_daily_task_X`
- **THEN** factor definitions for `daily_open`, `daily_high`, `daily_low`, `daily_close`, `daily_pre_close`, `daily_change`, `daily_pct_chg`, `daily_vol`, `daily_amount` SHALL exist in the database, and factor values for symbol X SHALL be stored

#### Scenario: User can customize symbol
- **WHEN** the user modifies the `SYMBOLS` variable at the top of the extension file
- **THEN** the task SHALL fetch and register data for the updated symbol(s)
