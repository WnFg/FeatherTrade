import logging
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import BaseFactorLogic

logger = logging.getLogger(__name__)

IDENTIFIER_COLUMNS = {'ts_code', 'trade_date', 'symbol', 'timestamp', 'date', 'code'}


@dataclass
class QuickRegisterConfig:
    """Declarative config for batch-registering DataFrame columns as factors."""
    data_source: str
    fields: Optional[List[str]] = None
    prefix: str = ""
    description_template: str = "Auto-registered factor for column '{field}'"
    category: str = "QuickRegister"


class ColumnExtractLogic(BaseFactorLogic):
    """Built-in factor logic that extracts a single named column from a DataFrame."""

    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        column = config.get("column")
        if not column:
            logger.error("ColumnExtractLogic: 'column' key missing from formula_config")
            return pd.DataFrame()

        if column not in data.columns:
            logger.error(f"ColumnExtractLogic: column '{column}' not found in DataFrame (columns: {list(data.columns)})")
            return pd.DataFrame()

        # Resolve symbol column
        if 'symbol' in data.columns:
            symbol_col = data['symbol']
        elif 'ts_code' in data.columns:
            symbol_col = data['ts_code']
        else:
            logger.error("ColumnExtractLogic: no symbol/ts_code column found")
            return pd.DataFrame()

        # Resolve timestamp column
        if 'timestamp' in data.columns:
            ts_col = data['timestamp'].apply(_parse_date)
        elif 'trade_date' in data.columns:
            ts_col = data['trade_date'].apply(_parse_date)
        else:
            logger.error("ColumnExtractLogic: no timestamp/trade_date column found")
            return pd.DataFrame()

        return pd.DataFrame({
            'timestamp': ts_col,
            'symbol': symbol_col,
            'value': data[column].astype(float),
        })


def _parse_date(value) -> datetime:
    """Parse YYYYMMDD string or passthrough datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and len(value) == 8 and value.isdigit():
        return datetime(int(value[:4]), int(value[4:6]), int(value[6:8]))
    # Fallback: try pandas
    return pd.Timestamp(value).to_pydatetime()


def detect_factor_columns(df: pd.DataFrame) -> List[str]:
    """Return numeric columns that are not identifier columns."""
    return [
        col for col in df.columns
        if col not in IDENTIFIER_COLUMNS and pd.api.types.is_numeric_dtype(df[col])
    ]
