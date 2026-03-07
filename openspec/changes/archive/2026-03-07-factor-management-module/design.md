## Context

The trading system currently lacks a centralized way to manage financial factors. Strategies often compute their own indicators internally, leading to redundant calculations and inconsistency. This design introduces a `FactorManager` that handles the entire lifecycle: definition, ingestion of raw data, calculation of factor values, storage in SQLite, and querying.

## Goals / Non-Goals

**Goals:**
- Implement a pluggable architecture for data sources (File, API).
- Implement a pluggable architecture for factor calculation logic (e.g., Simple Moving Average, RSI).
- Use SQLite for persistence as defined in `docs/factor_model.md`.
- Provide a high-level API for strategies to query factors.
- Ensure the module is decoupled from specific strategy logic.

**Non-Goals:**
- Real-time streaming factor calculation (initial focus is on batch/on-demand processing).
- Distributed storage or high-performance time-series database integration (sticking to SQLite for now).
- Complex cross-asset factor models (e.g., PCA across 500 stocks) in the first iteration.

## Decisions

### 1. Provider-Based Ingestion
**Decision**: Use an abstract `BaseDataSource` class with concrete implementations like `FileDataSource` and `APIDataSource`.
**Rationale**: This allows the system to easily support new data formats or APIs by just adding a new class.

### 2. Factor Calculation via "Compute Strategy" Pattern
**Decision**: Define a `BaseFactorLogic` class. Each factor (e.g., `VolatilityFactor`) implements a `compute(data)` method.
**Rationale**: Keeps the `FactorManager` thin. Users can add new factors by inheriting from `BaseFactorLogic` and registering them, requiring zero changes to the core `FactorManager` code.

### 3. SQLite for Persistence
**Decision**: Follow the schema in `docs/factor_model.md`.
**Rationale**: Leverages the pre-designed, extensible metadata/data separation which supports versioning and categorical organization.

### 4. Query Interface
**Decision**: Provide a `get_factor_values(symbol, factor_name, start_date, end_date)` method.
**Rationale**: Simple, intuitive, and covers the primary use case for strategy decision-making.

## Risks / Trade-offs

- **[Risk] SQLite Performance** → **Mitigation**: Use indexes on `(factor_id, symbol, timestamp)` and batch transactions for high-volume writes.
- **[Risk] Data Source Complexity** → **Mitigation**: Implement robust error handling and logging in the ingestion layer to handle network/file failures.
- **[Risk] Factor Logic Dependencies** → **Mitigation**: Ensure factor logic classes are stateless and rely only on the provided input data.
