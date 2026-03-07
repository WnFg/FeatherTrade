from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..data.factor_models import FactorValue, FactorDefinition

class BaseDataSource(ABC):
    """Abstract base class for all factor data sources (e.g., File, API)."""

    @abstractmethod
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Fetches raw data for a symbol within a time range."""
        pass

class BaseFactorLogic(ABC):
    """Abstract base class for factor calculation logic."""

    @abstractmethod
    def compute(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[FactorValue]:
        """Computes factor values from raw data using the provided configuration."""
        pass

class FactorRegistry:
    """High-level management of factor definitions."""
    def __init__(self, db):
        self.db = db

    def register_factor(self, definition: FactorDefinition) -> int:
        """Registers a new factor definition."""
        return self.db.insert_factor_definition(definition)

    def get_factor(self, name: str) -> Optional[FactorDefinition]:
        """Retrieves a factor definition."""
        return self.db.get_factor_definition(name)

    def list_factors(self, category: Optional[str] = None) -> List[FactorDefinition]:
        """Lists all registered factors."""
        return self.db.get_all_factor_definitions(category)

class FactorService:
    """Main interface for interacting with the factor system."""
    def __init__(self, db):
        self.db = db
        self.registry = FactorRegistry(db)
        self._logic_map: Dict[str, BaseFactorLogic] = {}
        self._source_map: Dict[str, BaseDataSource] = {}

    def register_logic(self, name: str, logic: BaseFactorLogic):
        self._logic_map[name] = logic

    def register_source(self, name: str, source: BaseDataSource):
        self._source_map[name] = source

    def get_factor_values(self, symbol: str, factor_name: str, 
                          start_time: Optional[datetime] = None, 
                          end_time: Optional[datetime] = None,
                          limit: Optional[int] = None) -> List[FactorValue]:
        """Queries factor values from the database."""
        return self.db.query_factor_values(factor_name, symbol, start_time, end_time, limit)

    def get_factor_values_by_category(self, symbol: str, category: str,
                                      start_time: Optional[datetime] = None,
                                      end_time: Optional[datetime] = None) -> Dict[str, List[FactorValue]]:
        """Queries multiple factor values for a symbol within a category."""
        factors = self.registry.list_factors(category)
        result = {}
        for f in factors:
            result[f.name] = self.get_factor_values(symbol, f.name, start_time, end_time)
        return result

    def compute_and_store_batch(self, symbols: List[str], factor_names: List[str], 
                                source_name: str, start_time: datetime, end_time: datetime):
        """Efficiently computes and stores multiple factors for multiple symbols."""
        # This implementation is a simple loop, but could be optimized for specific sources/logics
        for symbol in symbols:
            for factor_name in factor_names:
                self.compute_and_store(symbol, factor_name, source_name, start_time, end_time)

    def compute_and_store(self, symbol: str, factor_name: str, source_name: str,
                          start_time: datetime, end_time: datetime):
        """Coordinates data fetching, computation, and storage."""
        factor_def = self.registry.get_factor(factor_name)
        if not factor_def:
            raise ValueError(f"Factor {factor_name} not registered")

        source = self._source_map.get(source_name)
        if not source:
            raise ValueError(f"Source {source_name} not registered")

        logic = self._logic_map.get(factor_def.name)
        if not logic:
            # Fallback to category logic or error
            raise ValueError(f"No computation logic found for factor {factor_name}")

        raw_data = source.fetch_data(symbol, start_time, end_time)
        computed_values = logic.compute(raw_data, factor_def.formula_config)
        
        # Ensure factor_id is set
        for v in computed_values:
            v.factor_id = factor_def.id

        self.db.insert_factor_values(computed_values)

class FileDataSource(BaseDataSource):
    """Simple data source that reads raw data from a CSV file."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        import csv
        data = []
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic normalization for this sample implementation
                if row.get('symbol') != symbol:
                    continue
                
                ts = datetime.fromisoformat(row['timestamp'])
                if start_time <= ts <= end_time:
                    # Convert types as needed
                    row['price'] = float(row['price']) if 'price' in row else 0.0
                    row['timestamp'] = ts
                    data.append(row)
        return sorted(data, key=lambda x: x['timestamp'])

class APIDataSource(BaseDataSource):
    """Skeleton for an API-based data source."""
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        # In a real implementation, use requests or similar to fetch from the API
        # Example: requests.get(f"{self.base_url}/data?symbol={symbol}&start={start_time}&end={end_time}&key={self.api_key}")
        print(f"Fetch data from {self.base_url} for {symbol}")
        return []

class MovingAverageFactor(BaseFactorLogic):
    """Calculates a Simple Moving Average (SMA)."""
    def compute(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[FactorValue]:
        window = config.get('window', 20)
        price_key = config.get('price_key', 'price')
        
        computed = []
        prices = [d[price_key] for d in data]
        
        for i in range(len(data)):
            if i < window - 1:
                continue
            
            sma_val = sum(prices[i-window+1:i+1]) / window
            computed.append(FactorValue(
                id=None,
                factor_id=0, # To be set by Service
                symbol=data[i]['symbol'],
                timestamp=data[i]['timestamp'],
                value=sma_val
            ))
        return computed
