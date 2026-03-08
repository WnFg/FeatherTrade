## Context

The current trading system's factor management is monolithic, with all logic (data sources, factor calculations) residing in `src/trading_system/factors/service.py`. This tightly coupled architecture makes it difficult for users to add custom factors or data sources without modifying the core framework, increasing the risk of regressions and making it harder to maintain a clean codebase.

## Goals / Non-Goals

**Goals:**
- Decouple factor logic and data source implementations from the core `FactorService`.
- Establish a standard extension point for user-defined factors and data sources.
- Implement a dynamic registration mechanism to discover and load extensions at runtime.
- Maintain backward compatibility for existing scripts and configurations.

**Non-Goals:**
- Re-architecting the database schema for factor storage.
- Adding support for non-Python factor logic (e.g., C++ or Java).
- Changing the primary interface of `FactorService` (e.g., `compute_and_store`).

## Decisions

### 1. New Directory Structure
**Decision:** Move current implementations to `src/trading_system/factors/builtin/` and create `src/trading_system/factors/extensions/` for user code.
**Rationale:** This clearly distinguishes between framework-provided "standard" components and user-provided custom components. It allows for easier packaging and deployment of the core framework while giving users a safe place to put their code.
**Alternatives Considered:**
- Use a single directory for all factors: This would mix core code with user code, making updates harder.
- Use a completely separate package: This adds complexity to the Python environment configuration.

### 2. Dynamic Discovery via `FactorRegistry`
**Decision:** Enhance `FactorRegistry` to scan both the `builtin` and `extensions` directories for classes inheriting from `BaseFactorLogic` or `BaseDataSource`.
**Rationale:** This automates the registration process, meaning users only need to drop a new file into the extensions directory to make it available. It reduces the boilerplate required to "hook" new logic into the system.
**Alternatives Considered:**
- Manual registration in a config file: Error-prone and requires an extra step for the user.
- Explicit `import` in `service.py`: Requires modifying core code, defeating the purpose of the refactor.

### 3. Base Class Interface Refinement
**Decision:** Refine `BaseFactorLogic` and `BaseDataSource` in a new `src/trading_system/factors/base.py` module.
**Rationale:** Providing a stable, well-defined base class is crucial for a successful extension framework. Moving these to their own module prevents circular imports and provides a clean entry point for extension developers.
**Alternatives Considered:**
- Keeping base classes in `service.py`: Keeps the core file large and cluttered.

## Risks / Trade-offs

- **[Risk] Name Collisions**: Two extensions (one builtin, one user) might share the same name.
  - **Mitigation**: The registry will implement a namespacing strategy (e.g., `builtin.ma` vs `extensions.ma`) or prioritize user extensions over builtins.
- **[Risk] Performance Overhead of Scanning**: Dynamically scanning directories on every start might be slow.
  - **Mitigation**: Implement a cache for the registry or scan only once during the initial `FactorService` instantiation.
- **[Risk] Broken Extensions**: A malformed user extension could prevent the system from starting.
  - **Mitigation**: Use robust `try-except` blocks during discovery and load only valid extensions, logging errors for the ones that fail.
