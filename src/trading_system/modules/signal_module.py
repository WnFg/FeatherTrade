from abc import ABC, abstractmethod
from src.trading_system.core.event_engine import EventEngine

class AbstractSignalSource(ABC):
    """
    Abstract base class for all market data signal sources (e.g., Live, CSV).
    """
    def __init__(self, event_engine: EventEngine):
        self._event_engine = event_engine

    @abstractmethod
    def start(self):
        """Start the signal source feed."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the signal source feed."""
        pass
