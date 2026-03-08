import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class BaseDataSource(ABC):
    """Abstract base class for all factor data sources (e.g., File, API)."""

    @abstractmethod
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Fetches raw data for a symbol within a time range and returns a DataFrame."""
        pass

    def configure(self, params: Dict[str, Any]) -> None:
        """
        Configure the data source with runtime parameters.

        This method is called by DataSourceFactory after instantiation.
        Subclasses can override to accept configuration parameters.
        Default implementation does nothing (backward compatible).

        Args:
            params: Configuration parameters dictionary
        """
        pass

class BaseFactorLogic(ABC):
    """Abstract base class for factor calculation logic."""

    @abstractmethod
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Computes factor values from a DataFrame and returns a DataFrame.
        Expected columns in output: timestamp, value (and optionally symbol).
        """
        pass
