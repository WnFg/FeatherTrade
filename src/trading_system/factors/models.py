from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class FactorDefinition:
    """Metadata for a financial factor."""
    id: Optional[int]
    name: str
    display_name: str
    category: str
    description: str
    formula_config: Dict[str, Any]
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_json_config(self) -> str:
        return json.dumps(self.formula_config)

    @staticmethod
    def from_db_row(row: tuple) -> 'FactorDefinition':
        # Assuming row: (id, name, display_name, category, description, formula_config, version, created_at, updated_at)
        return FactorDefinition(
            id=row[0],
            name=row[1],
            display_name=row[2],
            category=row[3],
            description=row[4],
            formula_config=json.loads(row[5]) if row[5] else {},
            version=row[6],
            created_at=datetime.fromisoformat(row[7]) if isinstance(row[7], str) else row[7],
            updated_at=datetime.fromisoformat(row[8]) if isinstance(row[8], str) else row[8]
        )

@dataclass
class FactorValue:
    """A single computed factor value for a symbol at a point in time."""
    id: Optional[int]
    factor_id: int
    symbol: str
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = None

    def to_json_metadata(self) -> str:
        return json.dumps(self.metadata) if self.metadata else "{}"

    @staticmethod
    def from_db_row(row: tuple) -> 'FactorValue':
        # Assuming row: (id, factor_id, symbol, timestamp, value, metadata)
        return FactorValue(
            id=row[0],
            factor_id=row[1],
            symbol=row[2],
            timestamp=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
            value=row[4],
            metadata=json.loads(row[5]) if row[5] else {}
        )

@dataclass
class DataSourceInstance:
    """A configured data source template with parameters."""
    id: Optional[int]
    name: str
    class_path: str
    parameters: Dict[str, Any]
    transformation_config: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_json_params(self) -> str:
        return json.dumps(self.parameters)

    def to_json_transform(self) -> str:
        return json.dumps(self.transformation_config)

    @staticmethod
    def from_db_row(row: tuple) -> 'DataSourceInstance':
        return DataSourceInstance(
            id=row[0],
            name=row[1],
            class_path=row[2],
            parameters=json.loads(row[3]) if row[3] else {},
            transformation_config=json.loads(row[4]) if row[4] else {},
            created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            updated_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6]
        )

@dataclass
class ScheduledTask:
    """A task that links a factor with a data source and scheduling info."""
    id: Optional[int]
    factor_definition_id: int
    data_source_instance_id: int
    trigger_type: str
    trigger_config: Any
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_db_row(row: tuple) -> 'ScheduledTask':
        return ScheduledTask(
            id=row[0],
            factor_definition_id=row[1],
            data_source_instance_id=row[2],
            trigger_type=row[3],
            trigger_config=json.loads(row[4]) if row[4] and row[4].startswith('{') else row[4],
            is_active=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
            updated_at=datetime.fromisoformat(row[7]) if isinstance(row[7], str) else row[7]
        )

@dataclass
class TaskExecutionLog:
    """Execution history for a scheduled task."""
    id: Optional[int]
    task_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = 'PENDING'
    error_message: Optional[str] = None

    @staticmethod
    def from_db_row(row: tuple) -> 'TaskExecutionLog':
        return TaskExecutionLog(
            id=row[0],
            task_id=row[1],
            start_time=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
            end_time=datetime.fromisoformat(row[3]) if isinstance(row[3], str) and row[3] else row[3],
            status=row[4],
            error_message=row[5]
        )
