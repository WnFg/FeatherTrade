import logging
from typing import Dict, List, Any
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import (
    EventType, MarketEvent, FillEvent, EndOfBarEvent
)
from src.trading_system.modules.execution_engine import (
    AbstractExecutor, Order, OrderStatus, OrderType, Position, Side
)
from src.trading_system.data.market_data import Bar, Tick

logger = logging.getLogger(__name__)


class BacktestSimulator(AbstractExecutor):
    """
    Simulates a broker for backtesting.

    Fills orders based on incoming MarketEvents.
    All methods that mutate state (_pending_orders, _in_flight) are called
    exclusively from the EventEngine's single dispatch thread, so no
    additional locking is required for those structures.

    After processing all fills for a bar, emits an EndOfBarEvent so that
    subscribers (e.g. BacktestRecorder) can take a clean NAV snapshot.
    """

    def __init__(self, event_engine: EventEngine, account_service: Any = None):
        super().__init__(event_engine, account_service)
        # Keyed by order_id for O(1) lookup and removal
        self._pending_orders: Dict[str, Order] = {}
        self._current_prices: Dict[str, float] = {}
        # Local position tracking used when no AccountService is provided
        self._local_positions: Dict[str, Position] = {}

        self._event_engine.register(EventType.MARKET, self._on_market_event)
        # Update local positions on fills (works with or without AccountService)
        self._event_engine.register(EventType.FILL, self._on_fill_event)

    # ------------------------------------------------------------------
    # AbstractExecutor interface
    # ------------------------------------------------------------------

    def submit_order(self, order: Order):
        """
        Validate and enqueue an order.

        Pre-flight checks use the current known price.  A second check is
        performed at fill time to guard against the TOCTOU window between
        submission and the next MarketEvent.
        """
        if self.is_in_flight(order.strategy_id):
            logger.debug(
                "Simulator: IGNORED order %s from %s — order already IN_FLIGHT.",
                order.order_id, order.strategy_id,
            )
            return

        if self._account_service:
            if order.side == Side.BUY:
                price = self._current_prices.get(order.symbol, order.price or 0.0)
                estimated_cost = order.quantity * price
                if not self._account_service.has_funds(estimated_cost):
                    logger.warning(
                        "Simulator: REJECTED BUY order %s — insufficient funds "
                        "(need %.2f, have %.2f).",
                        order.order_id, estimated_cost, self._account_service.cash,
                    )
                    order.status = OrderStatus.REJECTED
                    return
            elif order.side == Side.SELL:
                if not self._account_service.has_position(order.symbol, order.quantity):
                    logger.warning(
                        "Simulator: REJECTED SELL order %s — insufficient position.",
                        order.order_id,
                    )
                    order.status = OrderStatus.REJECTED
                    return

        order.status = OrderStatus.PENDING
        self._pending_orders[order.order_id] = order
        self._in_flight.add(order.strategy_id)
        print(
            f"Simulator: Order submitted: {order.order_id} for "
            f"{order.symbol} ({order.side}) from {order.strategy_id}"
        )

    def cancel_order(self, order_id: str):
        """Cancel a pending order by ID."""
        order = self._pending_orders.pop(order_id, None)
        if order:
            order.status = OrderStatus.CANCELED
            self._in_flight.discard(order.strategy_id)
            print(f"Simulator: Order canceled: {order_id}")
        else:
            print(f"Simulator: Order not found for cancellation: {order_id}")

    def get_position(self, symbol: str) -> Position:
        """Return position from AccountService if available, otherwise from local tracker."""
        if self._account_service:
            return self._account_service.get_position(symbol)
        return self._local_positions.get(symbol, Position(symbol=symbol))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_market_event(self, event: MarketEvent) -> None:
        """Update price cache, check fills, then emit EndOfBarEvent."""
        data = event.data
        symbol = data.symbol

        if isinstance(data, Tick):
            price = data.price
        elif isinstance(data, Bar):
            price = data.close
        else:
            return

        self._current_prices[symbol] = price
        self._check_fills(symbol, price)
        # Notify subscribers that all fills for this bar have been enqueued
        self._event_engine.put(EndOfBarEvent(data))

    def _on_fill_event(self, event: FillEvent) -> None:
        """Maintain local position state (used when no AccountService is present)."""
        data = event.data
        symbol = data["symbol"]
        side: Side = data["side"]
        quantity: int = data["quantity"]
        price: float = data["price"]

        if symbol not in self._local_positions:
            self._local_positions[symbol] = Position(symbol=symbol)
        pos = self._local_positions[symbol]

        signed_qty = quantity if side == Side.BUY else -quantity
        if pos.quantity == 0:
            pos.quantity = signed_qty
            pos.average_cost = price
        elif (pos.quantity > 0 and signed_qty > 0) or (pos.quantity < 0 and signed_qty < 0):
            total_cost = (pos.quantity * pos.average_cost) + (signed_qty * price)
            pos.quantity += signed_qty
            pos.average_cost = total_cost / pos.quantity
        else:
            old_qty = pos.quantity
            pos.quantity += signed_qty
            if pos.quantity == 0:
                pos.average_cost = 0.0
            elif (old_qty * pos.quantity) < 0:
                pos.average_cost = price

    # ------------------------------------------------------------------
    # Fill logic
    # ------------------------------------------------------------------

    def _check_fills(self, symbol: str, price: float) -> None:
        """Try to fill all pending orders for *symbol* at *price*.

        For each fillable order:
        1. Determine the correct fill price (LIMIT orders honour the limit).
        2. Re-validate funds/position against AccountService (TOCTOU guard).
        3. Emit FillEvent and remove from pending list.
        """
        to_fill: List[str] = []

        for order_id, order in self._pending_orders.items():
            if order.symbol != symbol:
                continue

            can_fill = False
            fill_price = price

            if order.order_type == OrderType.MARKET:
                can_fill = True
                fill_price = price

            elif order.order_type == OrderType.LIMIT:
                if order.side == Side.BUY and price <= order.price:
                    can_fill = True
                    # Fill at the limit price (best guaranteed price for buyer)
                    fill_price = order.price
                elif order.side == Side.SELL and price >= order.price:
                    can_fill = True
                    fill_price = order.price

            elif order.order_type == OrderType.STOP:
                if order.side == Side.BUY and price >= order.price:
                    can_fill = True
                    fill_price = price
                elif order.side == Side.SELL and price <= order.price:
                    can_fill = True
                    fill_price = price

            if not can_fill:
                continue

            # --- TOCTOU guard: re-validate at actual fill price ---
            if self._account_service:
                if order.side == Side.BUY:
                    actual_cost = order.quantity * fill_price
                    if not self._account_service.has_funds(actual_cost):
                        logger.warning(
                            "Simulator: REJECTED BUY fill for order %s — "
                            "insufficient funds at fill price %.2f.",
                            order_id, fill_price,
                        )
                        order.status = OrderStatus.REJECTED
                        to_fill.append(order_id)   # remove from pending
                        self._in_flight.discard(order.strategy_id)
                        continue
                elif order.side == Side.SELL:
                    if not self._account_service.has_position(order.symbol, order.quantity):
                        logger.warning(
                            "Simulator: REJECTED SELL fill for order %s — "
                            "insufficient position.",
                            order_id,
                        )
                        order.status = OrderStatus.REJECTED
                        to_fill.append(order_id)
                        self._in_flight.discard(order.strategy_id)
                        continue

            order.status = OrderStatus.FILLED
            to_fill.append(order_id)
            self._in_flight.discard(order.strategy_id)

            self._event_engine.put(FillEvent({
                "order_id": order.order_id,
                "strategy_id": order.strategy_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "price": fill_price,
            }))

        for oid in to_fill:
            self._pending_orders.pop(oid, None)

    def flush_pending_orders(self) -> None:
        """Fill any remaining pending orders at the last known price.

        Called by BacktestRunner after the event queue is fully drained
        (i.e. after engine.stop()).  This handles orders that were submitted
        on the final bar, where no subsequent MarketEvent will arrive to
        trigger _check_fills.
        """
        for symbol, price in list(self._current_prices.items()):
            if any(o.symbol == symbol for o in self._pending_orders.values()):
                self._check_fills(symbol, price)
        # Drain the FillEvents we just put onto the (now-stopped) engine
        # by dispatching them synchronously.
        import queue as _queue
        while True:
            try:
                item = self._event_engine._queue.get_nowait()
            except _queue.Empty:
                break
            # Unwrap _PrioritizedEvent wrapper when engine is in time_ordered mode
            event = item.event if self._event_engine._time_ordered else item
            if event is None:
                # put it back so the engine sentinel is preserved
                self._event_engine._queue.put(item)
                break
            self._event_engine._dispatch(event)
            try:
                self._event_engine._queue.task_done()
            except ValueError:
                pass
