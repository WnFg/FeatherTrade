## ADDED Requirements

### Requirement: TuShare Daily Data Source Config
The extension SHALL define a `DataSourceConfig` named `"tushare_daily_X"` that uses `TuShareDataSource` with `api="daily"` and `symbols=["X"]`, covering a time range of approximately one year ending today.

#### Scenario: Data source config present
- **WHEN** `FactorService` initializes with this extension in the extensions directory
- **THEN** `service.registry.get_data_source_config("tushare_daily_X")` SHALL return the config

---

### Requirement: TuShare Daily Quick Register Config
The extension SHALL define a `QUICK_REGISTER_CONFIGS` entry with `data_source="tushare_daily_X"` and `fields=["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]`, using `prefix="daily_"` and `category="TuShareDaily"`.

#### Scenario: Factors auto-registered at startup
- **WHEN** `FactorService` initializes with this extension
- **THEN** factor definitions for `daily_open`, `daily_high`, `daily_low`, `daily_close`, `daily_pre_close`, `daily_change`, `daily_pct_chg`, `daily_vol`, `daily_amount` SHALL exist in the database

#### Scenario: Each factor has correct category
- **WHEN** `service.get_factor_definition("daily_close")` is called
- **THEN** the returned definition SHALL have `category="TuShareDaily"`

#### Scenario: Prefix applied to all factor names
- **WHEN** quick registration completes
- **THEN** all registered factor names SHALL start with `"daily_"`
