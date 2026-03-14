from __future__ import annotations

from datetime import datetime
from typing import List

import pandas as pd

from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import EventType, FillEvent, EndOfBarEvent
from src.trading_system.modules.account_service import AccountService
from src.trading_system.modules.execution_engine import Side
from src.trading_system.backtest.result import (
    BacktestResult,
    TradeRecord,
    compute_drawdown_curve,
    compute_metrics,
)


class BacktestRecorder:
    """
    Non-invasive recorder that subscribes to the EventEngine and collects:
    - Every FillEvent     → TradeRecord + avg-cost tracking
    - Every EndOfBarEvent → bar-by-bar equity / position snapshot

    NAV snapshots are taken on END_OF_BAR (fired by BacktestSimulator
    *after* all fills for that bar have been enqueued), so the snapshot
    always reflects the post-fill account state for that bar.

    Call build_result() after the backtest finishes to get a BacktestResult.
    """

    def __init__(
        self,
        event_engine: EventEngine,
        account_service: AccountService,
        symbol: str,
        initial_capital: float,
    ):
        self._event_engine = event_engine
        self._account_service = account_service
        self._symbol = symbol
        self._initial_capital = initial_capital

        # Internal accumulators
        self._bars: list = []
        self._timestamps: List[datetime] = []
        self._equity_points: List[float] = []
        self._position_points: List[int] = []
        self._trades: List[TradeRecord] = []

        # Track average cost per symbol for P&L calculation on SELL
        self._avg_cost: dict = {}

        # Register handlers
        # END_OF_BAR is fired after _check_fills, so AccountService state is current
        self._event_engine.register(EventType.END_OF_BAR, self._on_end_of_bar)
        self._event_engine.register(EventType.FILL, self._on_fill)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_end_of_bar(self, event: EndOfBarEvent) -> None:
        """Take a NAV snapshot after all fills for this bar have been applied."""
        bar = event.data

        # Validate bar (EndOfBarEvent carries the same Bar/Tick as MarketEvent)
        if not hasattr(bar, 'close') or bar.close <= 0:
            print(f"[BacktestRecorder] WARNING: invalid bar in END_OF_BAR, skipping. bar={bar}")
            return

        self._bars.append(bar)
        self._timestamps.append(bar.timestamp)

        # Current position qty (post-fill state)
        pos = self._account_service.get_position(bar.symbol)
        qty = pos.quantity if pos else 0
        self._position_points.append(qty)

        # Equity = cash + market value of positions (post-fill)
        equity = self._account_service.calculate_total_value(
            {bar.symbol: bar.close}
        )
        self._equity_points.append(equity)

    def _on_fill(self, event: FillEvent) -> None:
        """Record a trade fill and compute realised P&L for SELL fills."""
        data = event.data
        symbol = data["symbol"]
        side: Side = data["side"]
        quantity: int = data["quantity"]
        price: float = data["price"]

        # Timestamp: use last seen bar timestamp if available
        timestamp = self._timestamps[-1] if self._timestamps else datetime.utcnow()

        pnl = 0.0
        if side == Side.SELL:
            avg_cost = self._avg_cost.get(symbol, price)
            pnl = (price - avg_cost) * quantity
        else:
            # On BUY: read updated avg cost from AccountService (fill already applied)
            updated_pos = self._account_service.get_position(symbol)
            self._avg_cost[symbol] = updated_pos.average_cost

        self._trades.append(
            TradeRecord(
                timestamp=timestamp,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                pnl=pnl,
            )
        )

    # ------------------------------------------------------------------
    # Result construction
    # ------------------------------------------------------------------

    def build_result(self) -> BacktestResult:
        """Aggregate all collected data into a BacktestResult object."""
        if self._timestamps:
            index = pd.DatetimeIndex(self._timestamps)
            equity_curve = pd.Series(self._equity_points, index=index, name="equity")
            position_curve = pd.Series(self._position_points, index=index, name="position")
        else:
            equity_curve = pd.Series(dtype=float, name="equity")
            position_curve = pd.Series(dtype=int, name="position")

        drawdown_curve = compute_drawdown_curve(equity_curve)
        drawdown_curve.name = "drawdown"

        metrics = compute_metrics(equity_curve, self._trades, self._initial_capital)

        final_equity = (
            float(equity_curve.iloc[-1]) if not equity_curve.empty
            else self._initial_capital
        )

        return BacktestResult(
            symbol=self._symbol,
            initial_capital=self._initial_capital,
            final_cash=self._account_service.cash,
            final_equity=final_equity,
            trades=list(self._trades),
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            position_curve=position_curve,
            bars=list(self._bars),
            metrics=metrics,
        )
