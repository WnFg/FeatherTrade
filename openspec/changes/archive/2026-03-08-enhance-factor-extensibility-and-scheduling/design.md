## Context

The current trading system has a core `FactorService` and `FactorRegistry`, but they rely on static class definitions and manual registration. To allow users to define factors and ingestion tasks dynamically, we need a persistent metadata layer and an execution engine that can instantiate components based on database configurations.

## Goals / Non-Goals

**Goals:**
- Implement database-backed storage for factor definitions, data source instances, and scheduled tasks.
- Create a factory mechanism to instantiate `BaseDataSource` and `BaseFactorLogic` using parameters stored in the database.
- Develop a scheduling engine (e.g., using `APScheduler`) to execute factor computation tasks based on cron or one-off triggers.
- Support data transformation rules (column mapping, type casting) as part of the ingestion pipeline.

**Non-Goals:**
- Real-time factor computation (this design focuses on batch/scheduled ingestion).
- Distributed task execution (single-process scheduler is sufficient for the current scale).
- High-frequency data ingestion (data sources are assumed to be REST APIs or CSV files).

## Decisions

### 1. Database Schema for Metadata
**Decision:** Introduce three new tables: `factor_definitions`, `data_source_instances`, and `scheduled_tasks`.
**Rationale:** Standard normalization allows for flexible reuse of data sources across multiple factor tasks and clean tracking of task execution state.
**Alternatives Considered:**
- Storing everything in a single JSON blob: Harder to query and maintain data integrity.

### 2. Data Source Instance Factory
**Decision:** Store the class path (e.g., `src.trading_system.factors.builtin.data_sources.TuShareDataSource`) and a JSON blob of parameters in the `data_source_instances` table.
**Rationale:** This allows the system to dynamically instantiate the correct class with the user-provided parameters at runtime.
**Alternatives Considered:**
- Hardcoding specific parameters in the schema: Not extensible to new data source types.

### 3. Scheduling Engine Selection
**Decision:** Use `APScheduler` with a `SQLAlchemy` job store.
**Rationale:** `APScheduler` is a standard, lightweight Python library that supports cron-like scheduling and persistence of jobs. Using a database-backed job store ensures that tasks survive application restarts.
**Alternatives Considered:**
- Custom loop with `sleep`: Harder to implement cron logic correctly.
- `Celery`: Too heavy for the current requirements (requires a broker like Redis).

### 4. Transformation Logic Implementation
**Decision:** Implement transformation as a post-fetch hook in `FactorService`. The configuration will be stored as a dictionary in the `data_source_instances` metadata.
**Rationale:** Keeping transformation logic separate from the data source implementation allows the same raw data source to be adapted to different factor logic requirements.
**Alternatives Considered:**
- Embedding transformation in the data source class: Less flexible for users.

## Risks / Trade-offs

- **[Risk] Task Overlap**: Long-running factor computations might overlap if the schedule is too frequent.
  - **Mitigation**: Use `APScheduler`'s `coalesce` and `max_instances` settings to prevent concurrent execution of the same task.
- **[Risk] Parameter Mismatch**: Database parameters might not match the constructor of the data source class.
  - **Mitigation**: Implement a validation step during task creation/registration to check parameter compatibility.
- **[Risk] Database Contention**: Frequent status updates from the scheduler might lock tables.
  - **Mitigation**: Use separate tables for metadata (infrequent updates) and execution logs (frequent inserts).

## Migration Plan

1.  Update the database schema with new tables.
2.  Refactor `FactorRegistry` to query the database as a fallback if a static registration is not found.
3.  Implement the `TaskScheduler` and integrate it into the system startup sequence.
4.  Provide a utility/API to migrate existing static factor configurations to the database.
