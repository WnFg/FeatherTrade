from datetime import datetime
from typing import Any, Optional


class EventType:
    """Standardized event type strings."""
    MARKET = "market"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"
    RISK_SIGNAL = "risk_signal"
    END_OF_BAR = "end_of_bar"   # synthetic: fired after all fills for a bar are processed


# Priority ordering within the same timestamp:
# Lower number = dispatched first when timestamps are equal.
_EVENT_PRIORITY: dict = {
    EventType.MARKET:     0,
    EventType.END_OF_BAR: 1,
    EventType.SIGNAL:     2,
    EventType.RISK_SIGNAL:2,
    EventType.ORDER:      3,
    EventType.FILL:       4,
}


class Event:
    """Base class for all events.

    Parameters
    ----------
    type : str
        One of the EventType constants.
    data : Any
        Payload attached to the event.
    timestamp : datetime, optional
        Wall-clock / simulation time when the event *logically* occurs.
        When the EventEngine is configured for time-ordered dispatch
        (``time_ordered=True``) events are dequeued in ascending timestamp
        order.  Events with no timestamp are treated as occurring at the
        earliest possible time and maintain their insertion order among
        themselves.
    """

    def __init__(self, type: str, data: Any = None,
                 timestamp: Optional[datetime] = None):
        self.type = type
        self.data = data
        self.timestamp = timestamp


class MarketEvent(Event):
    """Event triggered by new market data (tick or bar)."""
    def __init__(self, data: Any):
        # Carry the bar/tick timestamp so the engine can sort by it.
        ts = getattr(data, 'timestamp', None)
        super().__init__(EventType.MARKET, data, timestamp=ts)


class SignalEvent(Event):
    """Event triggered by a strategy signal (BUY/SELL/HOLD)."""
    def __init__(self, data: Any, timestamp: Optional[datetime] = None):
        ts = timestamp or getattr(data, 'timestamp', None)
        super().__init__(EventType.SIGNAL, data, timestamp=ts)


class RiskSignalEvent(Event):
    """Event triggered by a risk strategy signal (e.g., Stop-Loss)."""
    def __init__(self, data: Any, timestamp: Optional[datetime] = None):
        ts = timestamp or getattr(data, 'timestamp', None)
        super().__init__(EventType.RISK_SIGNAL, data, timestamp=ts)


class OrderEvent(Event):
    """Event triggered by an order request."""
    def __init__(self, data: Any, timestamp: Optional[datetime] = None):
        ts = timestamp or getattr(data, 'timestamp', None)
        super().__init__(EventType.ORDER, data, timestamp=ts)


class FillEvent(Event):
    """Event triggered when an order is partially or fully filled."""
    def __init__(self, data: Any, timestamp: Optional[datetime] = None):
        ts = timestamp or (data.get('timestamp') if isinstance(data, dict) else None)
        super().__init__(EventType.FILL, data, timestamp=ts)


class EndOfBarEvent(Event):
    """Synthetic event fired by BacktestSimulator after all fills for a bar
    have been enqueued.  Subscribers (e.g. BacktestRecorder) can use this
    to take a net-asset-value snapshot after the bar's fills are applied."""
    def __init__(self, data: Any):
        ts = getattr(data, 'timestamp', None)
        super().__init__(EventType.END_OF_BAR, data, timestamp=ts)
