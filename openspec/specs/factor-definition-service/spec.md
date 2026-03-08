## ADDED Requirements

### Requirement: Persistent Factor Metadata Storage
The system SHALL provide a mechanism to persist factor definitions, including name, description, category, and calculation formula configuration.

#### Scenario: Registering a new factor definition
- **WHEN** a user provides a unique factor name, description, and formula configuration
- **THEN** the system SHALL store the definition in the database and return a unique identifier

### Requirement: Factor Definition Lookup
The system SHALL allow retrieving a factor definition by its unique name or identifier.

#### Scenario: Retrieving factor by name
- **WHEN** a user queries for a factor named 'moving_average'
- **THEN** the system SHALL return the full metadata for that factor if it exists

### Requirement: Handling Duplicate Factor Registration
The system SHALL ignore requests to register a factor name that already exists in the registry.

#### Scenario: Attempting to register existing factor
- **WHEN** a user attempts to register a factor with a name that is already in use
- **THEN** the system SHALL return the existing factor's ID and NOT create a new entry
