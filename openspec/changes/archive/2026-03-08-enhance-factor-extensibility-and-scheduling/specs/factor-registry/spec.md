## MODIFIED Requirements

### Requirement: Factor Definition Registry
The system SHALL provide a registry to define and manage factor metadata, including name, display name, category, and version. It SHALL support dynamic registration and lookup from the persistence layer.

#### Scenario: Successful factor registration with persistence
- **WHEN** a user registers a new factor with name 'rsi_14', category 'Momentum', and version '1.0.0'
- **THEN** the system SHALL persist the metadata to the database and assign a unique factor ID

### Requirement: Standardized Data Ingestion
The `FactorService` SHALL coordinate the ingestion of data from a `BaseDataSource` instance and its conversion into `FactorValue` storage, including handling user-defined parameter transformations.

#### Scenario: Ingesting data with parameter transformations
- **WHEN** `FactorService.compute_and_store` is called with a configured data source instance
- **THEN** it SHALL fetch the data, apply column mapping and type transformations, compute factors, and store results in the database
