## 1. Module Restructuring

- [x] 1.1 Create `src/trading_system/factors/base.py` and move `BaseDataSource` and `BaseFactorLogic` classes there.
- [x] 1.2 Create `src/trading_system/factors/builtin/` package (including `__init__.py`).
- [x] 1.3 Move `FileDataSource`, `APIDataSource`, and `TuShareDataSource` from `service.py` to `src/trading_system/factors/builtin/data_sources.py`.
- [x] 1.4 Move `MovingAverageFactor` from `service.py` to `src/trading_system/factors/builtin/factors.py`.
- [x] 1.5 Create `src/trading_system/factors/extensions/` directory for user-defined components.
- [x] 1.6 Update `src/trading_system/factors/service.py` imports to reflect the new structure.

## 2. Dynamic Registration Mechanism

- [x] 2.1 Implement a `DiscoveryEngine` (or similar utility) in `src/trading_system/factors/registry.py` to scan directories for subclasses of `BaseDataSource` and `BaseFactorLogic`.
- [x] 2.2 Enhance `FactorRegistry` to use the `DiscoveryEngine` to load components from both `builtin/` and `extensions/`.
- [x] 2.3 Add support for component namespacing (e.g., `builtin.ma` vs `extensions.ma`) in the registry.
- [x] 2.4 Implement error handling and logging for malformed or failing extension loads.

## 3. Factor Service Integration

- [x] 3.1 Update `FactorService.__init__` to initialize the enhanced `FactorRegistry`.
- [x] 3.2 Refactor `FactorService.compute_and_store` to retrieve logic and source instances dynamically from the registry.
- [x] 3.3 Ensure the `FactorService` maintains its existing public API for backward compatibility.

## 4. Verification and Documentation

- [x] 4.1 Create a unit test that verifies the `DiscoveryEngine` correctly identifies classes in a temporary directory.
- [x] 4.2 Implement an integration test with a sample extension in `src/trading_system/factors/extensions/` to verify the full "discovery-to-computation" pipeline.
- [x] 4.3 Update existing unit tests (`tests/unit/test_factor_system.py`) to work with the new module structure.
- [x] 4.4 Add a README or documentation snippet in `src/trading_system/factors/extensions/` explaining how users can add their own factors.
