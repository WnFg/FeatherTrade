## ADDED Requirements

### Requirement: Data Source Templates
The system SHALL provide a set of data source templates (e.g., TuShare, CSV File) that define required and optional configuration parameters.

#### Scenario: Listing available templates
- **WHEN** a user requests all available data source templates
- **THEN** the system SHALL return a list of templates including 'TuShareDataSource' and 'CSVFileDataSource'

### Requirement: Creating Data Source Instances
The system SHALL allow users to create 'Data Source Instances' by providing specific parameter values for a template.

#### Scenario: Instantiating a TuShare data source
- **WHEN** a user creates a 'TuShareDataSource' instance with `symbol='000001.SZ'`, `start_date='20230101'`, and `end_date='20230110'`
- **THEN** the system SHALL create an executable instance configured with those specific values

### Requirement: Parameter Transformation for Ingestion
The system SHALL support custom transformation logic (e.g., column renaming, type casting) for a data source instance to map raw data to a standardized format.

#### Scenario: Renaming raw data columns
- **WHEN** a user configures a transformation rule to map raw column 'ts_code' to 'symbol'
- **THEN** the system SHALL apply this renaming logic to the resulting DataFrame before factor computation
