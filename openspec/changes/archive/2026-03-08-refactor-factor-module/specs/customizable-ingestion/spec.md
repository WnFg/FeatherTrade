## MODIFIED Requirements

### Requirement: Customizable Data Source Factory
The system SHALL support creating data source instances with custom query parameters and strategies, either via database-persisted `DataSourceInstance` records or via in-memory `DataSourceConfig` objects.

#### Scenario: Instantiating TuShare with specific fields
- **WHEN** a user creates a `TuShareDataSource` with `fields=['trade_date', 'close', 'vol']` via `DataSourceConfig`
- **THEN** the instance SHALL only fetch those specific fields during data ingestion

#### Scenario: Instantiating from DataSourceConfig without DB
- **WHEN** a user defines a `DataSourceConfig` in an extension file and references it by name in a `ScheduleConfig`
- **THEN** the system SHALL instantiate the data source from the config without requiring a database record

### Requirement: Standardized Data Ingestion with Config-Driven Sources
The `FactorService` SHALL coordinate the ingestion of data from a `BaseDataSource` instance and its conversion into `FactorValue` storage, supporting both database-persisted instances and config-driven instances, and applying user-defined parameter transformations.

#### Scenario: Ingesting data with parameter transformations from config
- **WHEN** `FactorService.compute_and_store` is called with a data source name that resolves to a `DataSourceConfig`
- **THEN** it SHALL instantiate the source, fetch the data, apply column mapping and type transformations from the config, compute factors, and store results in the database

#### Scenario: Ingesting data from database-persisted instance
- **WHEN** `FactorService.compute_and_store` is called with a data source instance ID from the database
- **THEN** it SHALL load the instance, apply its stored transformation config, and proceed with factor computation
