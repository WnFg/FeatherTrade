# extension-framework Specification

## Purpose
Defines the extension points for the trading system: strategy extensions, adapter extensions, and factor/data-source extensions via the `extensions/` directory.

## Requirements

### Requirement: Document Strategy Extension
The documentation SHALL provide a guide on how to implement new trading strategies using the `BaseStrategy` interface.

#### Scenario: Strategy Implementation Guide
- **WHEN** the `docs/extension-guide.md` file is created
- **THEN** it SHALL include a step-by-step example of implementing `on_tick` and `on_bar`.

### Requirement: Document Adapter Extension
The documentation SHALL explain how to add new data source and execution adapters.

#### Scenario: Adapter Development Guide
- **WHEN** the adapter section is added to `docs/extension-guide.md`
- **THEN** it SHALL describe the interfaces for `AbstractSignalSource` and `AbstractExecutor`.

### Requirement: Factor Extension Point
The system SHALL provide a dedicated directory for user-defined factor logic and data sources.

#### Scenario: User adds a custom factor
- **WHEN** a user places a Python file containing a class inheriting from `BaseFactorLogic` into the `extensions/` directory
- **THEN** the system SHALL recognize and load this factor at runtime

### Requirement: Data Source Extension Point
The system SHALL provide a dedicated directory for user-defined data source implementations.

#### Scenario: User adds a custom data source
- **WHEN** a user places a Python file containing a class inheriting from `BaseDataSource` into the `extensions/` directory
- **THEN** the system SHALL recognize and load this data source at runtime

### Requirement: Dynamic Component Loading
The system MUST dynamically load extension classes during initialization without requiring modifications to the core framework code.

#### Scenario: Automatic discovery of extensions
- **WHEN** the `FactorService` initializes
- **THEN** it SHALL scan the configured extension directories and register all valid `BaseFactorLogic` and `BaseDataSource` subclasses

### Requirement: Component Namespacing
The system SHALL support namespacing for factors and data sources to distinguish between built-in and user-defined components.

#### Scenario: Built-in vs User components
- **WHEN** a factor named 'ma' exists in both `builtin/` and `extensions/` directories
- **THEN** the system SHALL provide a way to access both (e.g., via 'builtin.ma' and 'extensions.ma') or define a clear precedence (e.g., user extension overrides built-in)

