import sqlite3
import os
from typing import List, Optional, Tuple, Any
from datetime import datetime
import json
from .models import FactorDefinition, FactorValue, DataSourceInstance, ScheduledTask, TaskExecutionLog

class FactorDatabase:
    """Low-level SQLite database wrapper for factor data."""

    def __init__(self, db_path: str, schema_path: Optional[str] = None):
        self.db_path = db_path
        if schema_path is None:
            # Assume it's in the same directory as this file
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        self.schema_path = schema_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Initializes the database with the provided schema."""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found at {self.schema_path}")
            
        with open(self.schema_path, 'r') as f:
            schema_sql = f.read()
            
        with self._get_connection() as conn:
            conn.executescript(schema_sql)

    def insert_factor_definition(self, definition: FactorDefinition) -> int:
        """Inserts a new factor definition and returns its ID."""
        sql = """
        INSERT INTO factor_definitions (name, display_name, category, description, formula_config, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (
                definition.name,
                definition.display_name,
                definition.category,
                definition.description,
                definition.to_json_config(),
                definition.version
            ))
            return cursor.lastrowid

    def get_factor_definition(self, name: str) -> Optional[FactorDefinition]:
        """Retrieves a factor definition by its internal name."""
        sql = "SELECT * FROM factor_definitions WHERE name = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (name,))
            row = cursor.fetchone()
            if row:
                return FactorDefinition.from_db_row(row)
        return None

    def get_factor_definition_by_id(self, factor_id: int) -> Optional[FactorDefinition]:
        """Retrieves a factor definition by its ID."""
        sql = "SELECT * FROM factor_definitions WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (factor_id,))
            row = cursor.fetchone()
            if row:
                return FactorDefinition.from_db_row(row)
        return None

    def get_factor_definition_dict(self, name: str) -> Optional[dict]:
        """Retrieves a factor definition as a dictionary (for config-driven queries)."""
        factor_def = self.get_factor_definition(name)
        if not factor_def:
            return None
        return {
            'id': factor_def.id,
            'name': factor_def.name,
            'display_name': factor_def.display_name,
            'category': factor_def.category,
            'description': factor_def.description,
            'formula_config': factor_def.formula_config,
            'version': factor_def.version
        }

    def get_all_factor_definitions(self, category: Optional[str] = None) -> List[FactorDefinition]:
        """Retrieves all factor definitions, optionally filtered by category."""
        if category:
            sql = "SELECT * FROM factor_definitions WHERE category = ?"
            params = (category,)
        else:
            sql = "SELECT * FROM factor_definitions"
            params = ()
            
        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [FactorDefinition.from_db_row(row) for row in cursor.fetchall()]

    def insert_factor_values(self, values: List[FactorValue]):
        """Inserts multiple factor values in a single transaction."""
        sql = """
        INSERT INTO factor_values (factor_id, symbol, timestamp, value, metadata)
        VALUES (?, ?, ?, ?, ?)
        """
        data = [
            (v.factor_id, v.symbol, v.timestamp.isoformat() if isinstance(v.timestamp, datetime) else v.timestamp, v.value, v.to_json_metadata())
            for v in values
        ]
        with self._get_connection() as conn:
            conn.executemany(sql, data)

    def query_factor_values(self, factor_name: str, symbol: str, 
                            start_time: Optional[datetime] = None, 
                            end_time: Optional[datetime] = None,
                            limit: Optional[int] = None) -> List[FactorValue]:
        """Queries factor values for a specific factor and symbol with optional filters."""
        sql = """
        SELECT v.* FROM factor_values v
        JOIN factor_definitions f ON v.factor_id = f.id
        WHERE f.name = ? AND v.symbol = ?
        """
        params = [factor_name, symbol]

        if start_time:
            sql += " AND v.timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            sql += " AND v.timestamp <= ?"
            params.append(end_time.isoformat())
        
        sql += " ORDER BY v.timestamp DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [FactorValue.from_db_row(row) for row in cursor.fetchall()]

    # Data Source Instance methods
    def insert_data_source_instance(self, instance: DataSourceInstance) -> int:
        sql = """
        INSERT INTO data_source_instances (name, class_path, parameters, transformation_config)
        VALUES (?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (
                instance.name,
                instance.class_path,
                instance.to_json_params(),
                instance.to_json_transform()
            ))
            return cursor.lastrowid

    def get_data_source_instance(self, name_or_id: Any) -> Optional[DataSourceInstance]:
        if isinstance(name_or_id, int):
            sql = "SELECT * FROM data_source_instances WHERE id = ?"
        else:
            sql = "SELECT * FROM data_source_instances WHERE name = ?"
            
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (name_or_id,))
            row = cursor.fetchone()
            if row:
                return DataSourceInstance.from_db_row(row)
        return None

    def get_all_data_source_instances(self) -> List[DataSourceInstance]:
        sql = "SELECT * FROM data_source_instances"
        with self._get_connection() as conn:
            cursor = conn.execute(sql)
            return [DataSourceInstance.from_db_row(row) for row in cursor.fetchall()]

    # Scheduled Task methods
    def insert_scheduled_task(self, task: ScheduledTask) -> int:
        sql = """
        INSERT INTO scheduled_tasks (factor_definition_id, data_source_instance_id, trigger_type, trigger_config, is_active)
        VALUES (?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (
                task.factor_definition_id,
                task.data_source_instance_id,
                task.trigger_type,
                json.dumps(task.trigger_config) if isinstance(task.trigger_config, dict) else task.trigger_config,
                1 if task.is_active else 0
            ))
            return cursor.lastrowid

    def get_scheduled_task(self, task_id: int) -> Optional[ScheduledTask]:
        sql = "SELECT * FROM scheduled_tasks WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (task_id,))
            row = cursor.fetchone()
            if row:
                return ScheduledTask.from_db_row(row)
        return None

    def get_all_active_tasks(self) -> List[ScheduledTask]:
        sql = "SELECT * FROM scheduled_tasks WHERE is_active = 1"
        with self._get_connection() as conn:
            cursor = conn.execute(sql)
            return [ScheduledTask.from_db_row(row) for row in cursor.fetchall()]

    def update_task_status(self, task_id: int, is_active: bool):
        sql = "UPDATE scheduled_tasks SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        with self._get_connection() as conn:
            conn.execute(sql, (1 if is_active else 0, task_id))

    # Execution Log methods
    def insert_execution_log(self, log: TaskExecutionLog) -> int:
        sql = """
        INSERT INTO task_execution_logs (task_id, start_time, status)
        VALUES (?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (
                log.task_id,
                log.start_time.isoformat() if isinstance(log.start_time, datetime) else log.start_time,
                log.status
            ))
            return cursor.lastrowid

    def update_execution_log(self, log_id: int, end_time: datetime, status: str, error_message: Optional[str] = None):
        sql = """
        UPDATE task_execution_logs 
        SET end_time = ?, status = ?, error_message = ?
        WHERE id = ?
        """
        with self._get_connection() as conn:
            conn.execute(sql, (
                end_time.isoformat() if isinstance(end_time, datetime) else end_time,
                status,
                error_message,
                log_id
            ))

    def get_execution_history(self, task_id: int, limit: int = 10) -> List[TaskExecutionLog]:
        sql = """
        SELECT * FROM task_execution_logs 
        WHERE task_id = ? 
        ORDER BY start_time DESC 
        LIMIT ?
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (task_id, limit))
            return [TaskExecutionLog.from_db_row(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection (no-op for context-managed connections)."""
        pass
