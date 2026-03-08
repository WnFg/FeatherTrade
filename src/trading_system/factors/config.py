from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import json


@dataclass
class FactorConfig:
    """Configuration for a factor definition."""
    name: str
    category: str
    display_name: Optional[str] = None
    formula_config: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        data = asdict(self)
        # Convert formula_config to JSON string if needed for DB storage
        if self.formula_config:
            data['formula_config'] = json.dumps(self.formula_config)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FactorConfig':
        """Create from dictionary (YAML deserialization)."""
        data = data.copy()
        # Parse formula_config if it's a JSON string
        if isinstance(data.get('formula_config'), str):
            data['formula_config'] = json.loads(data['formula_config'])
        return cls(**data)


@dataclass
class DataSourceConfig:
    """Configuration for a data source instance."""
    name: str
    source_class: str
    params: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Dict[str, str]] = None
    transformation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSourceConfig':
        """Create from dictionary (YAML deserialization)."""
        return cls(**data)


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled task."""
    name: str
    factor: str  # Factor name or ID
    data_source: str  # DataSource config name
    trigger: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleConfig':
        """Create from dictionary (YAML deserialization)."""
        return cls(**data)
