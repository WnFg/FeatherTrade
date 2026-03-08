# Factor Extensibility and Scheduling

This document explains how to dynamically register factors, instantiate data sources, and schedule computation tasks.

## 1. Dynamic Factor Registration

You can register new factor definitions without modifying code by using the `FactorService.register_factor_definition` method or inserting into the `factor_definitions` table.

### Example (Python)
```python
from src.trading_system.factors.models import FactorDefinition

defn = FactorDefinition(
    id=None,
    name="my_new_factor",
    display_name="My New Factor",
    category="Custom",
    description="Description...",
    formula_config={"param1": 10}
)
service.register_factor_definition(defn)
```

## 2. Data Source Instantiation

Data sources can be created from templates with specific parameters. These are stored in the `data_source_instances` table.

### Example (SQL)
```sql
INSERT INTO data_source_instances (name, class_path, parameters, transformation_config)
VALUES (
    'aapl_daily_tushare',
    'TuShareDataSource',
    '{"symbol": "000001.SZ", "api_name": "daily"}',
    '{"column_mapping": {"ts_code": "symbol"}}'
);
```

### Parameter Transformation
The `transformation_config` field supports:
- `column_mapping`: Renames columns from the raw data.
- `type_casting`: Casts columns to `int`, `float`, or `datetime`.

## 3. Task Scheduling

Factor computation tasks link a factor definition with a data source instance and a trigger.

### Trigger Types
- `cron`: Standard cron expression (e.g., `0 9 * * *`).
- `interval`: Recurring at fixed intervals (e.g., `{"minutes": 30}`).
- `one-off`: Single execution at a specific time (ISO format).

### Example (Python)
```python
from src.trading_system.factors.models import ScheduledTask

task = ScheduledTask(
    id=None,
    factor_definition_id=1,
    data_source_instance_id=1,
    trigger_type='cron',
    trigger_config='0 9 * * *'
)
# Insert into DB and add to scheduler
db.insert_scheduled_task(task)
scheduler.add_task(task)
```

## 4. Execution Monitoring

Task runs are logged in the `task_execution_logs` table. You can check the status and any error messages there.

```sql
SELECT * FROM task_execution_logs WHERE task_id = 1 ORDER BY start_time DESC;
```
