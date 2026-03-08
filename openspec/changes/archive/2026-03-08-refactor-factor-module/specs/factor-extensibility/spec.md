## ADDED Requirements

### Requirement: Extension Directory Auto-Discovery
The system SHALL automatically discover `BaseFactorLogic` and `BaseDataSource` subclasses by scanning Python files placed in the `extensions/` directory, without requiring any manual registration calls.

#### Scenario: Dropping a new factor logic file
- **WHEN** a user places a Python file containing a `BaseFactorLogic` subclass in the `extensions/` directory and restarts `FactorService`
- **THEN** the system SHALL make that logic class available under its class name (lowercased) without any additional registration code

#### Scenario: Extension overrides builtin
- **WHEN** a user places a `BaseDataSource` subclass in `extensions/` with the same lowercased name as a builtin
- **THEN** the system SHALL use the extension class for the unprefixed name, while the builtin remains accessible via the `builtin.<name>` prefix

### Requirement: Declarative Config Variables in Extension Files
The system SHALL recognize module-level variables named `FACTOR_CONFIGS`, `DATA_SOURCE_CONFIGS`, and `SCHEDULE_CONFIGS` in extension Python files, and load them as declarative configuration at startup.

#### Scenario: Loading factor configs from extension file
- **WHEN** an extension file defines `FACTOR_CONFIGS = [FactorConfig(name="pe_ratio", ...)]`
- **THEN** the system SHALL register those factor definitions (upsert to `factor_definitions` table) during `FactorService` initialization

#### Scenario: Loading schedule configs from extension file
- **WHEN** an extension file defines `SCHEDULE_CONFIGS = [ScheduleConfig(name="daily_pe_job", ...)]`
- **THEN** the system SHALL register those tasks with the scheduler during initialization

### Requirement: YAML-Based Extension Configuration
The system SHALL support `.yaml` files in the `extensions/` directory as an alternative to Python files for declaring `FactorConfig`, `DataSourceConfig`, and `ScheduleConfig` entries.

#### Scenario: Loading factor config from YAML
- **WHEN** a user places a `my_factors.yaml` file in `extensions/` with a valid factor config structure
- **THEN** the system SHALL parse and register those factor definitions at startup, equivalent to the Python dict form

### Requirement: Framework and User Code Separation
The system SHALL enforce a clear boundary between framework-owned code (`builtin/`) and user-owned code (`extensions/`), such that users never need to modify files under `builtin/`.

#### Scenario: User adds factor without touching builtin
- **WHEN** a user wants to add a new factor type
- **THEN** they SHALL only need to create or modify files under `extensions/`, with no changes required to `builtin/` or any other framework file
