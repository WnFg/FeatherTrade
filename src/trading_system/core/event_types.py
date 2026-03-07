from typing import Any

class EventType:
    """Standardized event type strings."""
    MARKET = "market"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"
    RISK_SIGNAL = "risk_signal"

class Event:
    """Base class for all events."""
    def __init__(self, type: str, data: Any = None):
        self.type = type
        self.data = data

class MarketEvent(Event):
    """Event triggered by new market data (tick or bar)."""
    def __init__(self, data: Any):
        super().__init__(EventType.MARKET, data)

class SignalEvent(Event):
    """Event triggered by a strategy signal (BUY/SELL/HOLD)."""
    def __init__(self, data: Any):
        super().__init__(EventType.SIGNAL, data)

class RiskSignalEvent(Event):
    """Event triggered by a risk strategy signal (e.g., Stop-Loss)."""
    def __init__(self, data: Any):
        super().__init__(EventType.RISK_SIGNAL, data)

class OrderEvent(Event):
    """Event triggered by an order request."""
    def __init__(self, data: Any):
        super().__init__(EventType.ORDER, data)

class FillEvent(Event):
    """Event triggered when an order is partially or fully filled."""
    def __init__(self, data: Any):
        super().__init__(EventType.FILL, data)
