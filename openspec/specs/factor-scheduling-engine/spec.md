## ADDED Requirements

### Requirement: Factor Computation Task Creation
The system SHALL provide a mechanism for users to create and configure factor computation tasks that link a data source instance with a factor definition.

#### Scenario: Creating a new factor task
- **WHEN** a user creates a task for factor 'moving_average' using a configured 'TuShare' data source instance
- **THEN** the system SHALL store the task with its configuration and status

### Requirement: Scheduling Factor Tasks
The system SHALL support multiple scheduling types for factor tasks, including one-off execution and cron-based recurring execution.

#### Scenario: Scheduling a recurring cron task
- **WHEN** a user configures a task with the cron expression '0 9 * * *'
- **THEN** the system SHALL automatically trigger the task every day at 9:00 AM

### Requirement: Task Execution Monitoring and Status
The system SHALL track the execution history, status (e.g., PENDING, RUNNING, SUCCESS, FAILURE), and error logs for each scheduled task.

#### Scenario: Querying task execution history
- **WHEN** a user queries the execution history for a task ID
- **THEN** the system SHALL return a chronological list of all runs, their start/end times, and final status
