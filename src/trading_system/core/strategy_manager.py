import uuid
from typing import List
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import EventType, MarketEvent, SignalEvent, RiskSignalEvent
from src.trading_system.modules.execution_engine import AbstractExecutor, Order, OrderType, Side
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.data.market_data import Bar, Tick

class StrategyManager:
    """
    Coordinates between the EventEngine, SignalSources, and Executors.
    Dispatches market events to strategies and processes signals into orders.
    """
    def __init__(self, event_engine: EventEngine, executor: AbstractExecutor):
        self._event_engine = event_engine
        self._executor = executor
        self._strategies: List[BaseStrategy] = []

        # Register for market events to feed strategies
        self._event_engine.register(EventType.MARKET, self._on_market_event)

        # Register for signal events to convert them into orders
        self._event_engine.register(EventType.SIGNAL, self._on_signal_event)

        # Register for risk signal events to immediately close positions
        self._event_engine.register(EventType.RISK_SIGNAL, self._on_risk_signal_event)

    def add_strategy(self, strategy: BaseStrategy):
        """Adds a strategy to the manager."""
        self._strategies.append(strategy)

    def _on_market_event(self, event: MarketEvent):
        """Feeds market data to all registered strategies."""
        data = event.data
        for strategy in self._strategies:
            if isinstance(data, Tick):
                strategy.on_tick(data)
            elif isinstance(data, Bar):
                strategy.on_bar(data)

    def _on_signal_event(self, event: SignalEvent):
        """Converts a strategy signal into an order for the executor."""
        self._process_signal(event.data, "Strategy")

    def _on_risk_signal_event(self, event: RiskSignalEvent):
        """Converts a risk signal into an immediate market order."""
        self._process_signal(event.data, f"RiskManager ({event.data.get('action_type', 'UNKNOWN')})")

    def _process_signal(self, data: dict, source: str):
        """Helper to create and submit an order from signal data."""
        # Simplified: converting signal directly to a market order
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=data["symbol"],
            order_type=OrderType.MARKET,
            side=Side.BUY if data["side"].upper() == "BUY" else Side.SELL,
            quantity=data["quantity"],
            price=data.get("price", 0.0)
        )
        self._executor.submit_order(order)
        print(f"Manager: Signal from {source} converted to order: {order.order_id}")
