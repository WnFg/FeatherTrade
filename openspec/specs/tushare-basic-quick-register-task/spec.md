# tushare-basic-quick-register-task Specification

## Purpose
Defines the quick-register extension for TuShare A-share daily basic indicators (PE, PB, turnover rate, market cap, etc.) for a given symbol, enabling factor DB population via a single extension file drop.

## Requirements

### Requirement: TuShare Daily Basic Data Source Config
The extension SHALL define a `DataSourceConfig` named `"tushare_basic_Y"` that uses `TuShareDataSource` with `api="daily_basic"` and `symbols=["Y"]`, covering a time range of approximately one year ending today.

#### Scenario: Data source config present
- **WHEN** `FactorService` initializes with this extension in the extensions directory
- **THEN** `service.registry.get_data_source_config("tushare_basic_Y")` SHALL return the config

---

### Requirement: TuShare Daily Basic Quick Register Config
The extension SHALL define a `QUICK_REGISTER_CONFIGS` entry with `data_source="tushare_basic_Y"` and `fields=["close", "turnover_rate", "turnover_rate_f", "volume_ratio", "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm", "total_share", "float_share", "free_share", "total_mv", "circ_mv"]`, using `prefix="basic_"` and `category="TuShareBasic"`.

#### Scenario: Factors auto-registered at startup
- **WHEN** `FactorService` initializes with this extension
- **THEN** factor definitions for all prefixed fields (e.g. `basic_close`, `basic_pe`, `basic_pb`, etc.) SHALL exist in the database

#### Scenario: Each factor has correct category
- **WHEN** `service.get_factor_definition("basic_pe")` is called
- **THEN** the returned definition SHALL have `category="TuShareBasic"`

#### Scenario: Prefix applied to all factor names
- **WHEN** quick registration completes
- **THEN** all registered factor names SHALL start with `"basic_"`
