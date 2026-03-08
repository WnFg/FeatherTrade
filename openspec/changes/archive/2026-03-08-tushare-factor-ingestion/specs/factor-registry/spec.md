## MODIFIED Requirements

### Requirement: Factor Calculation Logic
The system SHALL provide a mechanism to compute factor values from raw market data. This logic MUST be encapsulated in classes that implement a standard interface.

#### Scenario: Computing SMA from DataFrame
- **WHEN** a `MovingAverageFactor` receives a `pandas.DataFrame` of prices
- **THEN** it SHALL return a list of `FactorValue` objects corresponding to the calculated SMA

### Requirement: Standardized Data Ingestion
The `FactorService` SHALL coordinate the ingestion of data from a `BaseDataSource` and its conversion into `FactorValue` storage.

#### Scenario: Ingesting and storing TuShare data
- **WHEN** `FactorService.compute_and_store` is called with a `TuShareDataSource`
- **THEN** it SHALL fetch the DataFrame, pass it to the logic class, and store the resulting factors in the database
