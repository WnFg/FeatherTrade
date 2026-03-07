from typing import List, Dict
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import EventType, MarketEvent, RiskSignalEvent
from src.trading_system.modules.account_service import AccountService
from src.trading_system.risk.base_risk import BaseRiskStrategy
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.modules.execution_engine import Side

class RiskManager:
    """
    Centralized risk management component.
    Evaluates active positions against loaded risk strategies.
    """
    def __init__(self, event_engine: EventEngine, account_service: AccountService):
        self._event_engine = event_engine
        self._account_service = account_service
        self._strategies: List[BaseRiskStrategy] = []
        
        # We need the latest prices to evaluate risk
        self._current_prices: Dict[str, float] = {}

        # Register to listen to market events for price updates
        self._event_engine.register(EventType.MARKET, self._on_market_event)

    def add_strategy(self, strategy: BaseRiskStrategy):
        """Adds a risk strategy to the manager."""
        self._strategies.append(strategy)

    def _on_market_event(self, event: MarketEvent):
        """Updates internal prices and evaluates risk."""
        data = event.data
        symbol = data.symbol
        
        if isinstance(data, Tick):
            price = data.price
        elif isinstance(data, Bar):
            price = data.close
        else:
            return

        self._current_prices[symbol] = price
        self._evaluate_risk(symbol, price)

    def _evaluate_risk(self, symbol: str, current_price: float):
        """Evaluates all risk strategies for a given symbol."""
        position = self._account_service.get_position(symbol)
        
        # Only evaluate if we have an active position
        if position.quantity == 0:
            return

        for strategy in self._strategies:
            action = strategy.evaluate(position, current_price)
            if action:
                self._trigger_risk_signal(symbol, position, action)
                break # Only trigger one risk signal per evaluation cycle

    def _trigger_risk_signal(self, symbol: str, position, action: str):
        """Emits a RiskSignalEvent to close the position."""
        # Determine the side needed to close the position
        side = "SELL" if position.quantity > 0 else "BUY"
        quantity = abs(position.quantity)

        signal_data = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "action_type": action, # e.g., 'STOP_LOSS', 'TAKE_PROFIT'
            "price": 0.0 # Market order
        }
        
        print(f"RiskManager: TRIGGERED {action} for {symbol}. Emitting RiskSignalEvent.")
        self._event_engine.put(RiskSignalEvent(signal_data))
