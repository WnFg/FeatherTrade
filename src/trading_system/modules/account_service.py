from typing import Dict, Any
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import EventType, FillEvent
from src.trading_system.modules.execution_engine import Position, Side

class AccountService:
    """
    Centralized service for managing funds and positions.
    Acts as the single source of truth for the account state.
    """
    def __init__(self, event_engine: EventEngine, initial_cash: float = 100000.0):
        self._event_engine = event_engine
        self._cash = initial_cash
        self._positions: Dict[str, Position] = {}
        
        # Register for fill events to update state
        self._event_engine.register(EventType.FILL, self._on_fill_event)

    @property
    def cash(self) -> float:
        return self._cash

    def has_funds(self, amount: float) -> bool:
        """Checks if the account has enough cash to cover an amount."""
        return self._cash >= amount

    def has_position(self, symbol: str, quantity: int) -> bool:
        """Checks if the account has enough quantity of a symbol to sell."""
        if symbol not in self._positions:
            return False
        return self._positions[symbol].quantity >= quantity

    def get_position(self, symbol: str) -> Position:
        """Returns the current position for a symbol."""
        return self._positions.get(symbol, Position(symbol=symbol))

    def _on_fill_event(self, event: FillEvent):
        """Processes a trade fill to update cash and positions."""
        data = event.data
        symbol = data["symbol"]
        side = data["side"]
        quantity = data["quantity"]
        price = data["price"]
        
        signed_qty = quantity if side == Side.BUY else -quantity
        cost = quantity * price
        
        # Update cash
        if side == Side.BUY:
            self._cash -= cost
        else:
            self._cash += cost
            
        # Update positions
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol)
        
        pos = self._positions[symbol]
        
        # Update average cost if increasing position in the same direction
        if (pos.quantity > 0 and signed_qty > 0) or (pos.quantity < 0 and signed_qty < 0):
            total_cost = (pos.quantity * pos.average_cost) + (signed_qty * price)
            pos.quantity += signed_qty
            pos.average_cost = total_cost / pos.quantity
        elif pos.quantity == 0:
            pos.quantity = signed_qty
            pos.average_cost = price
        else:
            # Reducing or flipping position
            old_qty = pos.quantity
            pos.quantity += signed_qty
            
            if pos.quantity == 0:
                pos.average_cost = 0.0
            elif (old_qty * pos.quantity) < 0:
                # Sign flipped (e.g., from Long to Short)
                pos.average_cost = price
            else:
                # Reducing position but same direction - cost doesn't change
                pass
        
        print(f"AccountService: Updated state after {side} fill for {symbol} at {price}. New Cash: {self._cash:.2f}, Position: {pos}")

    def calculate_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculates total equity (cash + market value of positions)."""
        asset_value = 0.0
        for symbol, pos in self._positions.items():
            if symbol in current_prices:
                asset_value += pos.quantity * current_prices[symbol]
        return self._cash + asset_value
