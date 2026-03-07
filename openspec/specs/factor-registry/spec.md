## ADDED Requirements

### Requirement: Factor Definition Registry
The system SHALL provide a registry to define and manage factor metadata, including name, display name, category, and version.

#### Scenario: Successful factor registration
- **WHEN** a user registers a new factor with name 'rsi_14', category 'Momentum', and version '1.0.0'
- **THEN** the system stores the metadata and assigns a unique factor ID

### Requirement: Factor Configuration Storage
The system SHALL allow storing factor-specific parameters (e.g., window size, smoothing period) as part of the factor definition.

#### Scenario: Registering factor with parameters
- **WHEN** a user registers a factor 'sma_20' with parameters '{"window": 20}'
- **THEN** the system stores the parameters alongside the factor definition

### Requirement: Factor Category Organization
The system SHALL support grouping factors into categories (e.g., Volatility, Momentum, Value) for easier discovery and management.

#### Scenario: Querying factors by category
- **WHEN** a user requests all factors in the 'Momentum' category
- **THEN** the system returns a list of all factors matching that category
