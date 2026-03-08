## ADDED Requirements

### Requirement: TuShare Data Source Integration
The system SHALL provide a builtin `TuShareDataSource` class that implements `BaseDataSource` and connects to the TuShare API using a token from the `TUSHARE_TOKEN` environment variable.

#### Scenario: TuShareDataSource fetches daily data
- **WHEN** a `TuShareDataSource` is configured with `api="daily"` and `symbol="000001.SZ"`, and `fetch_data()` is called
- **THEN** it SHALL call `tushare.pro_api().daily(ts_code="000001.SZ", ...)` and return the result as a pandas DataFrame

### Requirement: Daily Line Data Support
The system SHALL support fetching A-share daily line data (OHLCV) via TuShare's `daily` API endpoint.

#### Scenario: Fetching daily OHLCV for a symbol
- **WHEN** a user configures a `TuShareDataSource` with `api="daily"`, `symbol="600000.SH"`, and a date range
- **THEN** the system SHALL return a DataFrame with columns `ts_code`, `trade_date`, `open`, `high`, `low`, `close`, `vol`, `amount`

### Requirement: Daily Basic Metrics Support
The system SHALL support fetching daily valuation metrics (PE, PB, turnover rate, etc.) via TuShare's `daily_basic` API endpoint.

#### Scenario: Fetching PE and PB for a symbol
- **WHEN** a user configures a `TuShareDataSource` with `api="daily_basic"`, `symbol="000001.SZ"`, and `fields=["pe", "pb"]`
- **THEN** the system SHALL return a DataFrame with columns `ts_code`, `trade_date`, `pe`, `pb`

### Requirement: TuShare Token Configuration
The system SHALL read the TuShare API token from the `TUSHARE_TOKEN` environment variable, and SHALL raise an error if the variable is not set when a `TuShareDataSource` is instantiated.

#### Scenario: Missing TUSHARE_TOKEN raises error
- **WHEN** a user attempts to instantiate a `TuShareDataSource` and the `TUSHARE_TOKEN` environment variable is not set
- **THEN** the system SHALL raise a configuration error with a message indicating the missing token

### Requirement: TuShare Date Format Handling
The system SHALL convert TuShare's `YYYYMMDD` date format to standard `datetime` objects in the returned DataFrame.

#### Scenario: Converting trade_date to datetime
- **WHEN** TuShare returns a `trade_date` column with values like `"20240315"`
- **THEN** the system SHALL convert it to a `datetime` object (or keep as string if transformation config specifies otherwise)
