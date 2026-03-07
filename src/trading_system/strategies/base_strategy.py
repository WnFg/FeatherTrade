from abc import ABC, abstractmethod
from typing import Any, Dict
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import SignalEvent
from src.trading_system.data.market_data import Bar, Tick

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    """
    def __init__(self, event_engine: EventEngine, params: Dict[str, Any] = None):
        self._event_engine = event_engine
        self._params = params or {}
        self.active = False

    @abstractmethod
    def on_tick(self, tick: Tick):
        """Called when a new tick is received."""
        pass

    @abstractmethod
    def on_bar(self, bar: Bar):
        """Called when a new bar is received."""
        pass

    def send_signal(self, symbol: str, side: str, quantity: int, price: float = 0.0):
        """Sends a SignalEvent to the engine."""
        signal_data = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price
        }
        self._event_engine.put(SignalEvent(signal_data))
        print(f"Strategy: Signal sent: {signal_data}")
