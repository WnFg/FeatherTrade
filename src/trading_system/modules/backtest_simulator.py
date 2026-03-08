from typing import Dict, List, Any
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import EventType, FillEvent, MarketEvent
from src.trading_system.modules.execution_engine import AbstractExecutor, Order, OrderStatus, OrderType, Position, Side
from src.trading_system.data.market_data import Bar, Tick

class BacktestSimulator(AbstractExecutor):
    """
    Simulates a broker for backtesting. 
    Fills orders based on incoming MarketEvents.
    Synchronously validates orders via AccountService.
    """
    def __init__(self, event_engine: EventEngine, account_service: Any = None):
        super().__init__(event_engine, account_service)
        self._pending_orders: List[Order] = []
        self._current_prices: Dict[str, float] = {}
        
        # Register for market data to trigger fills
        self._event_engine.register(EventType.MARKET, self._on_market_event)

    def submit_order(self, order: Order):
        """
        Validates the order via AccountService and adds it to the pending list.
        Filters if strategy has an order IN_FLIGHT.
        """
        if self.is_in_flight(order.strategy_id):
            print(f"Simulator: IGNORED order {order.order_id} from {order.strategy_id} - Order already IN_FLIGHT.")
            return

        if self._account_service:
            # 2.2 Synchronous check for funds/positions
            if order.side == Side.BUY:
                # Estimate cost at current price or last known price
                price = self._current_prices.get(order.symbol, order.price or 0.0)
                estimated_cost = order.quantity * price
                if not self._account_service.has_funds(estimated_cost):
                    print(f"Simulator: REJECTED BUY order {order.order_id} - Insufficient funds.")
                    order.status = OrderStatus.REJECTED
                    return
            elif order.side == Side.SELL:
                if not self._account_service.has_position(order.symbol, order.quantity):
                    print(f"Simulator: REJECTED SELL order {order.order_id} - Insufficient position.")
                    order.status = OrderStatus.REJECTED
                    return

        order.status = OrderStatus.PENDING
        self._pending_orders.append(order)
        self._in_flight.add(order.strategy_id)
        print(f"Simulator: Order submitted: {order.order_id} for {order.symbol} ({order.side}) from {order.strategy_id}")

    def cancel_order(self, order_id: str):
        """Cancels an order from the pending list."""
        for order in self._pending_orders:
            if order.order_id == order_id:
                order.status = OrderStatus.CANCELED
                self._pending_orders.remove(order)
                if order.strategy_id in self._in_flight:
                    self._in_flight.remove(order.strategy_id)
                print(f"Simulator: Order canceled: {order_id}")
                return
        print(f"Simulator: Order not found for cancellation: {order_id}")

    def _on_market_event(self, event: MarketEvent):
        """Processes a MarketEvent to update prices and check fills."""
        data = event.data
        symbol = data.symbol
        
        # Update current price based on Tick or Bar
        if isinstance(data, Tick):
            price = data.price
        elif isinstance(data, Bar):
            price = data.close  # Simplified: using close for fill check
        else:
            return

        self._current_prices[symbol] = price
        self._check_fills(symbol, price)

    def _check_fills(self, symbol: str, price: float):
        """Checks if any pending orders can be filled at the current price."""
        filled_orders = []
        for order in self._pending_orders:
            if order.symbol != symbol:
                continue

            can_fill = False
            fill_price = price

            if order.order_type == OrderType.MARKET:
                can_fill = True
            elif order.order_type == OrderType.LIMIT:
                if order.side == Side.BUY and price <= order.price:
                    can_fill = True
                elif order.side == Side.SELL and price >= order.price:
                    can_fill = True
            elif order.order_type == OrderType.STOP:
                if order.side == Side.BUY and price >= order.price:
                    can_fill = True
                elif order.side == Side.SELL and price <= order.price:
                    can_fill = True

            if can_fill:
                order.status = OrderStatus.FILLED
                filled_orders.append(order)
                if order.strategy_id in self._in_flight:
                    self._in_flight.remove(order.strategy_id)
                
                # Notify the system about the fill
                # This triggers AccountService to update its state
                self._event_engine.put(FillEvent({
                    "order_id": order.order_id,
                    "strategy_id": order.strategy_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": order.quantity,
                    "price": fill_price
                }))

        # Remove filled orders from pending
        for order in filled_orders:
            self._pending_orders.remove(order)

    def get_position(self, symbol: str) -> Position:
        """Returns the current position for a symbol from AccountService."""
        if self._account_service:
            return self._account_service.get_position(symbol)
        return Position(symbol=symbol)
