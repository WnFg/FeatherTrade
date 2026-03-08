## ADDED Requirements

### Requirement: Config-Driven Factor Registration
The system SHALL support registering factor definitions via `FactorConfig` dataclass instances or YAML files, in addition to the existing database API.

#### Scenario: Registering factor from FactorConfig
- **WHEN** a user defines a `FactorConfig(name="pe_ratio", category="Value", formula_config={"field": "pe"})` in an extension file
- **THEN** the system SHALL upsert this definition to the `factor_definitions` table during initialization

#### Scenario: Idempotent config-based registration
- **WHEN** a `FactorConfig` with an existing factor name is loaded on multiple startups
- **THEN** the system SHALL update the existing record if changed, or skip if identical, without creating duplicates

## MODIFIED Requirements

### Requirement: Factor Definition Registry
The system SHALL provide a registry to define and manage factor metadata, including name, display name, category, and version. It SHALL support dynamic registration and lookup from the persistence layer, as well as declarative registration via config files.

#### Scenario: Successful factor registration with persistence
- **WHEN** a user registers a new factor with name 'rsi_14', category 'Momentum', and version '1.0.0' via `FactorConfig` or database API
- **THEN** the system SHALL persist the metadata to the database and assign a unique factor ID

#### Scenario: Loading factor definitions from extensions directory
- **WHEN** `FactorService` initializes and scans the `extensions/` directory
- **THEN** it SHALL discover all `FACTOR_CONFIGS` variables and YAML files, and register those factor definitions to the database
