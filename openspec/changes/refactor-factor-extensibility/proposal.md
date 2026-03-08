## Why

The current factor management code is concentrated in `src/trading_system/factors/service.py`, making it difficult for users to add new data sources or factor logic without modifying core framework files. To improve extensibility and maintainability, we need a modular structure that allows users to define custom extensions in a dedicated directory while the framework provides clean base classes and registration mechanisms.

## What Changes

- **Module Reorganization**: Move factor logic and data source implementations out of `service.py` into specialized sub-packages.
- **User Extension Point**: Establish a `user` or `extensions` directory (e.g., `src/trading_system/factors/extensions/`) where users can add their own `DataSource` and `FactorLogic` classes.
- **Dynamic Registration**: Enhance the `FactorService` or a dedicated `Registry` to support discovering and loading user-defined extensions dynamically.
- **Cleaner Core**: `service.py` will focus on the orchestration and storage logic, remaining agnostic of specific factor implementations.
- **Example Implementation**: Retain simplified examples in the user-extension directory to serve as templates.

## Capabilities

### New Capabilities
- `factor-extension-framework`: Modular structure and dynamic loading mechanism for user-defined factor components.

### Modified Capabilities
- `factor-registry`: Update the registry logic to support discovery from the extension directory.

## Impact

- **`src/trading_system/factors/`**: Significant directory structure changes.
- **Existing Factors/Sources**: `MovingAverageFactor`, `FileDataSource`, and `TuShareDataSource` will be moved to new locations.
- **API Stability**: The `FactorService` interface will remain largely consistent, but instantiation might change to reflect the new registry logic.
