from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.modules.execution_engine import Position

class BaseRiskStrategy(ABC):
    """
    Abstract base class for all pluggable risk management strategies.
    """
    def __init__(self, params: Dict[str, Any] = None):
        self._params = params or {}

    @abstractmethod
    def evaluate(self, position: Position, current_price: float) -> Optional[str]:
        """
        Evaluates a position against the risk rules.
        
        Args:
            position: The current active position.
            current_price: The latest market price for the asset.
            
        Returns:
            A string indicating the action to take (e.g., 'SELL_ALL', 'BUY_COVER') 
            or None if no action is required.
        """
        pass
