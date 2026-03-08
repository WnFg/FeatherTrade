import uuid
from typing import List, Dict, Optional, Any
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import EventType, MarketEvent, SignalEvent, RiskSignalEvent
from src.trading_system.modules.execution_engine import AbstractExecutor, Order, OrderType, Side
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.strategies.context import StrategyContext
from src.trading_system.data.market_data import Bar, Tick

class StrategyManager:
    """
    Coordinates between the EventEngine, SignalSources, and Executors.
    Dispatches market events to strategies and processes signals into orders.
    """
    def __init__(self, 
                 event_engine: EventEngine, 
                 executor: AbstractExecutor,
                 account_service: Optional[Any] = None,
                 factor_service: Optional[Any] = None):
        self._event_engine = event_engine
        self._executor = executor
        self._account_service = account_service
        self._factor_service = factor_service
        self._strategies: List[BaseStrategy] = []
        self._contexts: Dict[str, StrategyContext] = {}

        # Register for market events to feed strategies
        self._event_engine.register(EventType.MARKET, self._on_market_event)

        # Register for signal events to convert them into orders
        self._event_engine.register(EventType.SIGNAL, self._on_signal_event)

        # Register for risk signal events to immediately close positions
        self._event_engine.register(EventType.RISK_SIGNAL, self._on_risk_signal_event)

        # Dispatch fill events back to originating strategy
        self._event_engine.register(EventType.FILL, self._on_fill_event)

    def add_strategy(self, strategy: BaseStrategy):
        """Adds a strategy to the manager and initializes its context."""
        self._strategies.append(strategy)
        self._contexts[strategy.strategy_id] = StrategyContext(
            strategy_id=strategy.strategy_id,
            account_service=self._account_service,
            execution_engine=self._executor,
            factor_service=self._factor_service
        )

    def _on_market_event(self, event: MarketEvent):
        """Feeds market data to all registered strategies."""
        data = event.data
        for strategy in self._strategies:
            context = self._contexts.get(strategy.strategy_id)
            if isinstance(data, Tick):
                strategy.on_tick(data, context)
            elif isinstance(data, Bar):
                strategy.on_bar(data, context)

    def _on_signal_event(self, event: SignalEvent):
        """Converts a strategy signal into an order for the executor."""
        self._process_signal(event.data, "Strategy")

    def _on_risk_signal_event(self, event: RiskSignalEvent):
        """Converts a risk signal into an immediate market order."""
        self._process_signal(event.data, f"RiskManager ({event.data.get('action_type', 'UNKNOWN')})")

    def _on_fill_event(self, event):
        """Routes fill events back to the originating strategy's on_fill hook."""
        data = event.data
        strategy_id = data.get("strategy_id") or data.get("order_id", "")
        # Find by strategy_id in fill data (set by BacktestSimulator)
        for strategy in self._strategies:
            if strategy.strategy_id == data.get("strategy_id"):
                strategy.on_fill(data)
                return

    def _process_signal(self, data: dict, source: str):
        """Helper to create and submit an order from signal data."""
        # Simplified: converting signal directly to a market order
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=data["symbol"],
            order_type=OrderType.MARKET,
            side=Side.BUY if data["side"].upper() == "BUY" else Side.SELL,
            quantity=data["quantity"],
            strategy_id=data.get("strategy_id", "Unknown"),
            price=data.get("price", 0.0)
        )
        self._executor.submit_order(order)
        print(f"Manager: Signal from {source} converted to order: {order.order_id}")
