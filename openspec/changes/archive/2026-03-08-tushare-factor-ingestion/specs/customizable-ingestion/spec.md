## ADDED Requirements

### Requirement: Customizable Data Source Factory
The system SHALL support creating data source instances with custom query parameters and strategies.

#### Scenario: Instantiating TuShare with specific fields
- **WHEN** a user creates a `TuShareDataSource` with `fields=['trade_date', 'close', 'vol']`
- **THEN** the instance SHALL only fetch those specific fields during data ingestion

### Requirement: Strategy-Driven Data Ingestion
The system SHALL allow defining data source instances that target specific data endpoints (e.g., 'daily', 'adj_factor', 'income') based on the required factor logic.

#### Scenario: Generating a data source for corporate actions
- **WHEN** a user instantiates a data source with the 'adj_factor' strategy
- **THEN** it SHALL query the corresponding TuShare API to retrieve adjustment factors
