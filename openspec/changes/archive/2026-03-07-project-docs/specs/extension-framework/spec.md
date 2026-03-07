## ADDED Requirements

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
