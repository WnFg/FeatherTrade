  
- [x] 1.1 Create `factor_definitions` table to store factor metadata and formula configurations
- [x] 1.2 Create `data_source_instances` table to store template references and parameter JSON
- [x] 1.3 Create `scheduled_tasks` table to link factors with data source instances and store cron/trigger config
- [x] 1.4 Create `task_execution_logs` table to track task runs, status, and error messages
- [x] 1.5 Update `src/trading_system/factors/database.py` with SQLAlchemy models and DAO methods for new tables

## 2. Factor Definition & Service Enhancements

- [x] 2.1 Refactor `FactorRegistry` to support loading definitions from the database as a primary or fallback source
- [x] 2.2 Implement `FactorService.register_factor_definition` to persist new factor metadata
- [x] 2.3 Add support for looking up factor definitions by name or ID via the registry

## 3. Data Source Instantiation & Transformation

- [x] 3.1 Implement `DataSourceFactory` to dynamically instantiate `BaseDataSource` classes using stored parameters
- [x] 3.2 Add a registry of available data source templates (e.g., TuShare, CSV)
- [x] 3.3 Implement `ParameterTransformer` utility for column mapping and type casting
- [x] 3.4 Update `FactorService.compute_and_store` to accept a data source instance ID and apply transformations after fetching

## 4. Scheduling Engine Implementation

- [x] 4.1 Integrate `APScheduler` with a SQLAlchemy job store for persistence
- [x] 4.2 Create `TaskScheduler` class to manage task creation, scheduling, and manual triggers
- [x] 4.3 Implement task execution wrapper that handles status updates, error logging, and execution history
- [x] 4.4 Add cron parsing and validation for recurring tasks

## 5. Integration & Verification

- [x] 5.1 Create integration tests for the full pipeline: Create Factor -> Create DS Instance -> Schedule Task -> Verify Run
- [x] 5.2 Verify `APScheduler` persists and resumes tasks after system restart
- [x] 5.3 Test parameter transformation logic with a sample TuShare query (e.g., renaming `ts_code` to `symbol`)
- [x] 5.4 Document the new extensibility mechanism and scheduling API
