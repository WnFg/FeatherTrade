## MODIFIED Requirements

### Requirement: Factor Definition Registry
The system SHALL provide a registry to define and manage factor metadata, including name, display name, category, and version. It SHALL also manage the registration of both built-in and user-defined component classes.

#### Scenario: Successful factor registration from extensions
- **WHEN** a user registers a new factor with name 'custom_rsi', category 'Momentum', and version '1.0.0' located in the extensions directory
- **THEN** the registry SHALL store the metadata and the reference to the extension class

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
