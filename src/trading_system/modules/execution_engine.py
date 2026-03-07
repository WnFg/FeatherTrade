from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any
from src.trading_system.core.event_engine import EventEngine

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    symbol: str
    order_type: OrderType
    side: Side
    quantity: int
    price: float = 0.0  # Limit or Stop price
    status: OrderStatus = OrderStatus.PENDING

@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    quantity: int = 0
    average_cost: float = 0.0

class AbstractExecutor(ABC):
    """
    Abstract base class for all order executors (e.g., Live, Simulator).
    """
    def __init__(self, event_engine: EventEngine, account_service: Any = None):
        self._event_engine = event_engine
        self._account_service = account_service

    @abstractmethod
    def submit_order(self, order: Order):
        """Submit a new order for execution."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str):
        """Cancel an existing order."""
        pass
