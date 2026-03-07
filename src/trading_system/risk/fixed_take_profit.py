from typing import Dict, Any, Optional
from src.trading_system.risk.base_risk import BaseRiskStrategy
from src.trading_system.modules.execution_engine import Position

class FixedTakeProfitStrategy(BaseRiskStrategy):
    """
    Triggers a close out if the position gains a fixed percentage 
    of its average cost.
    """
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        # Default take profit percentage is 10%
        self._take_profit_pct = self._params.get("take_profit_pct", 0.10)

    def evaluate(self, position: Position, current_price: float) -> Optional[str]:
        if position.quantity == 0 or position.average_cost == 0:
            return None

        # Calculate percentage change
        if position.quantity > 0:
            profit_pct = (current_price - position.average_cost) / position.average_cost
        else:
            profit_pct = (position.average_cost - current_price) / position.average_cost
            
        if profit_pct >= self._take_profit_pct:
            return "TAKE_PROFIT"
            
        return None
