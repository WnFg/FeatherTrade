from typing import Dict, Any, Optional
from src.trading_system.risk.base_risk import BaseRiskStrategy
from src.trading_system.modules.execution_engine import Position

class FixedStopLossStrategy(BaseRiskStrategy):
    """
    Triggers a close out if the position loses a fixed percentage 
    of its average cost.
    """
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        # Default stop loss percentage is 5%
        self._stop_loss_pct = self._params.get("stop_loss_pct", 0.05)

    def evaluate(self, position: Position, current_price: float) -> Optional[str]:
        if position.quantity == 0 or position.average_cost == 0:
            return None

        # Calculate percentage change
        # If long, profit = (current - cost) / cost
        # If short, profit = (cost - current) / cost
        
        if position.quantity > 0:
            profit_pct = (current_price - position.average_cost) / position.average_cost
        else:
            profit_pct = (position.average_cost - current_price) / position.average_cost
            
        if profit_pct <= -self._stop_loss_pct:
            return "STOP_LOSS"
            
        return None
