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
