## ADDED Requirements

### Requirement: Declarative Data Source Config
The system SHALL allow users to describe a data source instance using a `DataSourceConfig` dataclass or equivalent YAML structure, specifying the source class, target symbols, time range, and optional column transformations — without writing to the database.

#### Scenario: Defining a TuShare daily_basic config in code
- **WHEN** a user declares a `DataSourceConfig` with `source_class="TuShareDataSource"`, `params={"api": "daily_basic", "symbols": ["000001.SZ", "600000.SH"]}`, and `time_range={"start": "today-3d", "end": "today"}`
- **THEN** the system SHALL be able to instantiate and execute that data source without any prior database writes

### Requirement: Relative Time Range Expressions
The system SHALL support relative time range expressions in `DataSourceConfig.time_range`, resolved to concrete `datetime` values at execution time.

#### Scenario: Resolving today-3d expression
- **WHEN** a data source config specifies `start: "today-3d"` and `end: "today"`
- **THEN** the system SHALL resolve these to the current date minus 3 calendar days and the current date respectively, at the moment of execution

#### Scenario: Accepting fixed ISO date strings
- **WHEN** a data source config specifies `start: "2024-01-01"` and `end: "2024-12-31"`
- **THEN** the system SHALL use those fixed dates without any relative resolution

### Requirement: Multi-Symbol Data Source Config
The system SHALL support specifying a list of stock symbols in `DataSourceConfig`, and the system SHALL fetch data for each symbol independently.

#### Scenario: Config with multiple symbols
- **WHEN** a `DataSourceConfig` specifies `symbols: ["000001.SZ", "600000.SH", "00700.HK"]`
- **THEN** the system SHALL execute the data source fetch for each symbol and process them individually

### Requirement: Column Transformation Config
The system SHALL support declaring column rename and type-cast rules in `DataSourceConfig.transformation`, applied to the raw DataFrame before factor computation.

#### Scenario: Renaming ts_code to symbol
- **WHEN** a `DataSourceConfig` declares `transformation: {rename: {ts_code: symbol, trade_date: timestamp}}`
- **THEN** the system SHALL rename those columns in the fetched DataFrame before passing it to factor logic

### Requirement: BaseDataSource Parameter Injection
The system SHALL support a `configure(params: dict)` method on `BaseDataSource` subclasses, called by the factory after instantiation to inject runtime parameters.

#### Scenario: Factory configures a data source instance
- **WHEN** `DataSourceFactory` instantiates a `TuShareDataSource` from a `DataSourceConfig`
- **THEN** it SHALL call `configure(params)` on the instance with the config's `params` dict before returning it
