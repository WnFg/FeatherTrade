from dataclasses import dataclass
from datetime import datetime

@dataclass
class Tick:
    """Normalized tick data."""
    symbol: str
    timestamp: datetime
    price: float
    volume: int

@dataclass
class Bar:
    """Normalized OHLCV bar data."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
