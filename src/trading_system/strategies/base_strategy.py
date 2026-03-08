from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import SignalEvent
from src.trading_system.data.market_data import Bar, Tick
from .context import StrategyContext

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    """
    def __init__(self, event_engine: EventEngine, params: Dict[str, Any] = None):
        self._event_engine = event_engine
        self._params = params or {}
        self.active = False
        self._strategy_id: str = self._params.get("strategy_id", self.__class__.__name__)

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @abstractmethod
    def on_tick(self, tick: Tick, context: StrategyContext):
        """Called when a new tick is received."""
        pass

    @abstractmethod
    def on_bar(self, bar: Bar, context: StrategyContext):
        """Called when a new bar is received."""
        pass

    def on_fill(self, fill_data: Dict[str, Any]):
        """
        Called when an order for this strategy is filled.

        Override in subclasses to react to fills (e.g. update position tracking).
        Default implementation is a no-op.
        """
        pass

    def send_signal(self, symbol: str, side: str, quantity: int, price: float = 0.0):
        """Sends a SignalEvent to the engine."""
        signal_data = {
            "strategy_id": self.strategy_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price
        }
        self._event_engine.put(SignalEvent(signal_data))
        print(f"Strategy {self.strategy_id}: Signal sent: {signal_data}")
