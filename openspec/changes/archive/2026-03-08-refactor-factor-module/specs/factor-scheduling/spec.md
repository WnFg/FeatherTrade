## ADDED Requirements

### Requirement: Declarative Schedule Config
The system SHALL allow users to define scheduled factor computation tasks using a `ScheduleConfig` dataclass or YAML structure, linking a factor, data source, and trigger specification.

#### Scenario: Defining a daily cron job in code
- **WHEN** a user declares a `ScheduleConfig` with `name="daily_pe_job"`, `factor="pe_ratio"`, `data_source="tushare_daily_basic"`, and `trigger={"type": "cron", "expr": "0 18 * * 1-5"}`
- **THEN** the system SHALL register this task with APScheduler to run at 18:00 on weekdays

### Requirement: Cron-Based Scheduling
The system SHALL support cron expressions for recurring task triggers, parsed and executed by APScheduler.

#### Scenario: Cron job fires at scheduled time
- **WHEN** a `ScheduleConfig` specifies `trigger: {type: "cron", expr: "0 9 * * *"}`
- **THEN** the system SHALL execute the associated factor computation task every day at 09:00

### Requirement: Interval-Based Scheduling
The system SHALL support interval-based triggers (e.g., every N hours/minutes) for recurring tasks.

#### Scenario: Interval job fires every 6 hours
- **WHEN** a `ScheduleConfig` specifies `trigger: {type: "interval", hours: 6}`
- **THEN** the system SHALL execute the task every 6 hours from the time the scheduler starts

### Requirement: One-Off Task Execution
The system SHALL support one-time task execution at a specified future datetime.

#### Scenario: One-off task at specific time
- **WHEN** a `ScheduleConfig` specifies `trigger: {type: "one-off", run_date: "2024-12-31T23:59:00"}`
- **THEN** the system SHALL execute the task once at that datetime and not repeat

### Requirement: Task Execution Logging
The system SHALL record each task execution in a `task_execution_logs` table, capturing start time, end time, status (RUNNING/SUCCESS/FAILURE), and error messages.

#### Scenario: Successful task execution logged
- **WHEN** a scheduled task completes successfully
- **THEN** the system SHALL insert a log entry with status 'SUCCESS', start time, and end time

#### Scenario: Failed task execution logged with error
- **WHEN** a scheduled task raises an exception during execution
- **THEN** the system SHALL insert a log entry with status 'FAILURE' and the exception message

### Requirement: Dynamic Symbol and Time Range Resolution
The system SHALL resolve the symbol list and time range from the associated `DataSourceConfig` at task execution time, not at task registration time.

#### Scenario: Task uses current date for relative time range
- **WHEN** a scheduled task executes with a data source config specifying `time_range: {start: "today-3d", end: "today"}`
- **THEN** the system SHALL compute the actual date range at the moment of execution, not when the task was registered

### Requirement: Manual Task Trigger
The system SHALL provide a method to manually trigger a scheduled task immediately, bypassing its normal schedule.

#### Scenario: User manually triggers a task
- **WHEN** a user calls `TaskScheduler.trigger_now(task_id)`
- **THEN** the system SHALL execute that task immediately in addition to its regular schedule
