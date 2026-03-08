## Context

The current factor system uses a list of dictionaries for data exchange between sources and logic. To support professional data providers like TuShare and leverage powerful data manipulation tools, we are transitioning to a `pandas.DataFrame` based architecture. This will also enable more complex data ingestion strategies beyond simple file reads.

## Goals / Non-Goals

**Goals:**
- Standardization: All `BaseDataSource` implementations must return `pd.DataFrame`.
- professional Integration: Provide a robust `TuShareDataSource` using the official SDK.
- Flexibility: Allow data sources to be instantiated with dynamic query "strategies" (endpoints, fields, filters).
- Efficiency: Leverage `pandas` for batch processing during factor calculation.

**Non-Goals:**
- Real-time streaming data ingestion (focus is on historical/batch ingestion).
- Automated database schema migrations for new factor types (metadata-driven only).

## Decisions

### 1. DataFrame-Centric Interface
**Decision**: Refactor `BaseDataSource.fetch_data` and `BaseFactorLogic.compute` to use `pandas.DataFrame`.
**Rationale**: DataFrames are the industry standard for financial time-series data in Python, offering superior performance and developer ergonomics compared to lists of dictionaries.

### 2. Strategy-Based `TuShareDataSource`
**Decision**: The `TuShareDataSource` will take an `api_name` (e.g., 'daily', 'income') and a `params` dictionary during initialization.
**Rationale**: This "factory" approach allows a single class to support hundreds of TuShare endpoints without subclassing for every new data type. 

### 3. DataFrame to `FactorValue` Mapping
**Decision**: Implement a generic mapper in `FactorService` that converts DataFrame rows into `FactorValue` objects for database storage.
**Rationale**: Centralizing the mapping logic reduces duplication in factor logic classes and ensures consistent metadata handling.

### 4. Dependency on `tushare` and `pandas`
**Decision**: Add `tushare` and `pandas` as core dependencies for the factor module.
**Rationale**: Essential for the proposed architecture.

## Risks / Trade-offs

- **[Risk] TuShare API Limits** → **Mitigation**: Implement basic error handling for rate limits and suggest batching strategies in documentation.
- **[Risk] Column Name Mismatch** → **Mitigation**: Define a standard set of "internal" column names (e.g., `symbol`, `timestamp`) and require sources to perform renaming if necessary.
- **[Risk] Breaking Change** → **Mitigation**: Update all existing data sources (`FileDataSource`) and logic (`MovingAverageFactor`) in this single change.
