## Why

The current factor management system lacks a formalized and extensible mechanism for users to register new factors, data sources, and automated scheduling tasks. To support professional trading workflows, users need the ability to dynamically define factor metadata, instantiate data sources with custom parameters, and configure automated ingestion/computation pipelines without modifying the core system code.

## What Changes

- **Factor Definition Registry**: Implement a mechanism to register and persist new factor definitions, including their calculation logic and configuration.
- **Data Source Templates and Instantiation**: Introduce "Data Source Templates" that define required parameters, allowing users to create multiple "Data Source Instances" with specific settings (e.g., symbol, API keys, date ranges).
- **Scheduling Engine Integration**: Add support for factor computation tasks that can be triggered on a schedule (Cron) or as one-off jobs.
- **Parameter Transformation Logic**: Allow users to define data transformation rules (e.g., column renaming, type casting) to map raw data source output to the format expected by factor logic.
- **State Management for Tasks**: Track the execution history and status of scheduled factor computation jobs.

## Capabilities

### New Capabilities
- `factor-definition-service`: Management and persistence of user-defined factor metadata and calculation logic.
- `data-source-instantiation`: Framework for creating executable data source instances from templates with specific parameters.
- `factor-scheduling-engine`: Automated execution of data fetching and factor computation tasks based on cron or manual triggers.

### Modified Capabilities
- `factor-registry`: Update to handle dynamic registration and lookups for the new definition service.

## Impact

- **`src/trading_system/factors/`**: New modules for definition storage and scheduling.
- **`src/trading_system/data/`**: Enhanced data source abstractions to support parameter-based instantiation.
- **Database Schema**: New tables for factor definitions, data source instances, and scheduled tasks.
