## ADDED Requirements

### Requirement: QuickRegisterConfig
The system SHALL provide a `QuickRegisterConfig` dataclass that users can declare in their extension files (alongside `FACTOR_CONFIGS`, `DATA_SOURCE_CONFIGS`, `SCHEDULE_CONFIGS`) to describe a batch factor registration from a DataFrame data source.

`QuickRegisterConfig` SHALL support the following fields:
- `data_source`: str — name of a registered `DataSourceConfig`
- `fields`: Optional[List[str]] — explicit list of column names to register as factors; if omitted, all non-identifier numeric columns are auto-detected
- `prefix`: Optional[str] — string prepended to each factor name (e.g. `"daily_"` → factor name `"daily_close"`)
- `description_template`: Optional[str] — template string for factor description; `{field}` is substituted with the column name
- `category`: Optional[str] — factor category applied to all registered factors; defaults to `"QuickRegister"`

#### Scenario: Config with explicit fields
- **WHEN** a `QuickRegisterConfig` specifies `fields=["close", "vol"]`
- **THEN** only factors for `close` and `vol` SHALL be registered, regardless of other columns in the DataFrame

#### Scenario: Config with prefix
- **WHEN** a `QuickRegisterConfig` specifies `prefix="daily_"`
- **THEN** the registered factor names SHALL be `"daily_close"`, `"daily_vol"`, etc.

#### Scenario: Config without fields (auto-detect)
- **WHEN** a `QuickRegisterConfig` omits `fields`
- **THEN** the system SHALL auto-detect all numeric columns from the data source, excluding identifier columns (`ts_code`, `trade_date`, `symbol`, `timestamp`, `date`)

---

### Requirement: Auto-Detection of Numeric Columns
The system SHALL automatically identify which columns in a DataFrame returned by a data source are eligible for factor registration.

Eligible columns SHALL satisfy:
1. Not in the identifier exclusion list: `ts_code`, `trade_date`, `symbol`, `timestamp`, `date`, `code`
2. Have a numeric dtype (int or float)

Column detection SHALL occur by fetching a small sample from the data source or by inspecting the DataFrame schema if available without a network call.

#### Scenario: OHLCV data source auto-detection
- **WHEN** a TuShare daily data source returns columns `[ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount]`
- **THEN** the auto-detected eligible columns SHALL be `[open, high, low, close, pre_close, change, pct_chg, vol, amount]`

#### Scenario: All columns are identifiers
- **WHEN** a DataFrame contains only identifier columns
- **THEN** the system SHALL register zero factors and log a warning

---

### Requirement: ColumnExtractLogic
The system SHALL provide a built-in `ColumnExtractLogic` class that implements `BaseFactorLogic` and extracts a single named column from a DataFrame as factor values.

`ColumnExtractLogic` SHALL be configured via `formula_config` with key `"column"` specifying which column to extract.

The `compute` method SHALL:
1. Verify the target column exists in the input DataFrame
2. Map the symbol identifier column (`ts_code` or `symbol`) to `symbol` output
3. Map the date column (`trade_date` or `timestamp`) to `timestamp` output, converting `YYYYMMDD` strings to `datetime` objects
4. Return a DataFrame with columns `[timestamp, symbol, value]`

#### Scenario: Successful column extraction
- **WHEN** `ColumnExtractLogic` with `config={"column": "close"}` receives a DataFrame with columns `[ts_code, trade_date, close]`
- **THEN** it SHALL return a DataFrame with `timestamp` (datetime), `symbol` (str), `value` (float) rows

#### Scenario: Missing column
- **WHEN** the target column does not exist in the DataFrame
- **THEN** `ColumnExtractLogic.compute` SHALL return an empty DataFrame and log an error

#### Scenario: YYYYMMDD date parsing
- **WHEN** the `trade_date` column contains strings in `YYYYMMDD` format (e.g. `"20180718"`)
- **THEN** the output `timestamp` column SHALL contain `datetime(2018, 7, 18)` objects

---

### Requirement: FactorService.quick_register
The system SHALL provide a `quick_register(config: QuickRegisterConfig)` method on `FactorService` that:
1. Resolves the data source by `config.data_source` name
2. Determines the set of factor fields (explicit or auto-detected)
3. For each field, registers a `FactorDefinition` in the database (idempotent — skip if already exists)
4. Binds a `ColumnExtractLogic` instance (configured with the field name) as the runtime logic for that factor
5. Returns a list of registered factor names

#### Scenario: Quick register from TuShare data source
- **WHEN** `service.quick_register(QuickRegisterConfig(data_source="tushare_daily"))` is called
- **THEN** factor definitions for all eligible columns SHALL be created in the database
- **AND** each factor SHALL be queryable via `service.get_factor_definition(name)`

#### Scenario: Idempotent registration
- **WHEN** `quick_register` is called twice with the same config
- **THEN** no duplicate factor definitions SHALL be created
- **AND** the method SHALL succeed without error

#### Scenario: Returns registered names
- **WHEN** `quick_register` completes
- **THEN** it SHALL return a list of the factor names that were registered (or already existed)

---

### Requirement: QUICK_REGISTER_CONFIGS Discovery
The system SHALL discover `QuickRegisterConfig` entries from extension files via the existing `DiscoveryEngine`.

If a Python extension file or YAML config file contains a module-level variable `QUICK_REGISTER_CONFIGS` (a list of `QuickRegisterConfig`), the `FactorRegistry` SHALL collect and expose these configs.

`FactorService.__init__` SHALL automatically call `quick_register` for each discovered `QuickRegisterConfig` during initialization.

#### Scenario: Auto-discovery at startup
- **WHEN** an extension file defines `QUICK_REGISTER_CONFIGS = [QuickRegisterConfig(data_source="my_source")]`
- **THEN** on `FactorService` initialization, the corresponding factors SHALL be auto-registered without any additional user code

#### Scenario: Missing data source reference
- **WHEN** a `QuickRegisterConfig` references a data source name that is not registered
- **THEN** the system SHALL log an error and skip that config without raising an exception
