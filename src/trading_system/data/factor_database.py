import sqlite3
import os
from typing import List, Optional, Tuple
from datetime import datetime
from .factor_models import FactorDefinition, FactorValue

class FactorDatabase:
    """Low-level SQLite database wrapper for factor data."""

    def __init__(self, db_path: str, schema_path: Optional[str] = None):
        self.db_path = db_path
        if schema_path is None:
            # Assume it's in the same directory as this file
            schema_path = os.path.join(os.path.dirname(__file__), 'factor_schema.sql')
        
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
