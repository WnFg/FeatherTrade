"""Unit tests for BacktestRecorder."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.trading_system.backtest.recorder import BacktestRecorder
from src.trading_system.backtest.result import TradeRecord
from src.trading_system.core.event_types import EventType, FillEvent, EndOfBarEvent
from src.trading_system.modules.execution_engine import Position, Side


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_bar(symbol="AAPL", close=100.0, ts=None):
    bar = MagicMock()
    bar.symbol = symbol
    bar.close = close
    bar.timestamp = ts or datetime(2024, 1, 1)
    return bar


def _make_fill_event(symbol="AAPL", side=Side.BUY, quantity=100, price=100.0):
    return FillEvent({
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "order_id": "test-order",
        "strategy_id": "test-strategy",
    })


def _make_recorder(initial_cash=100_000.0, symbol="AAPL"):
    """Return a recorder with mocked engine and account_service."""
    engine = MagicMock()
    account_service = MagicMock()
    account_service.cash = initial_cash
    account_service.get_position.return_value = Position(symbol=symbol, quantity=0, average_cost=0.0)
    account_service.calculate_total_value.return_value = initial_cash
    recorder = BacktestRecorder(engine, account_service, symbol, initial_cash)
    return recorder, account_service


# ---------------------------------------------------------------------------
# 6.1 — _on_fill correctly records TradeRecord
# ---------------------------------------------------------------------------

class TestOnFill:
    def test_buy_fill_creates_trade_record(self):
        recorder, acct = _make_recorder()
        # Simulate a bar timestamp being recorded first
        recorder._timestamps.append(datetime(2024, 1, 2))
        acct.get_position.return_value = Position(symbol="AAPL", quantity=100, average_cost=100.0)

        event = _make_fill_event(side=Side.BUY, quantity=100, price=100.0)
        recorder._on_fill(event)

        assert len(recorder._trades) == 1
        trade = recorder._trades[0]
        assert trade.side == Side.BUY
        assert trade.quantity == 100
        assert trade.price == 100.0
        assert trade.pnl == 0.0  # BUY fills have pnl=0

    def test_sell_fill_calculates_pnl(self):
        recorder, acct = _make_recorder()
        recorder._timestamps.append(datetime(2024, 1, 3))
        # Set up a known avg cost
        recorder._avg_cost["AAPL"] = 90.0
        acct.get_position.return_value = Position(symbol="AAPL", quantity=0, average_cost=0.0)

        event = _make_fill_event(side=Side.SELL, quantity=100, price=110.0)
        recorder._on_fill(event)

        assert len(recorder._trades) == 1
        trade = recorder._trades[0]
        assert trade.side == Side.SELL
        assert abs(trade.pnl - 2000.0) < 0.01  # (110 - 90) * 100

    def test_multiple_fills_accumulated(self):
        recorder, acct = _make_recorder()
        recorder._timestamps.append(datetime(2024, 1, 2))
        acct.get_position.return_value = Position(symbol="AAPL", quantity=100, average_cost=100.0)

        for _ in range(3):
            recorder._on_fill(_make_fill_event(side=Side.BUY, quantity=100, price=100.0))

        assert len(recorder._trades) == 3


# ---------------------------------------------------------------------------
# 6.2 — _on_market equity series length & no-position equity == cash
# ---------------------------------------------------------------------------

class TestOnEndOfBar:
    def test_equity_series_length_equals_bar_count(self):
        recorder, acct = _make_recorder(initial_cash=50_000.0)
        acct.calculate_total_value.return_value = 50_000.0
        acct.get_position.return_value = Position(symbol="AAPL", quantity=0, average_cost=0.0)

        n = 10
        for i in range(n):
            bar = _make_bar(close=100.0 + i, ts=datetime(2024, 1, 1) + timedelta(days=i))
            recorder._on_end_of_bar(EndOfBarEvent(bar))

        assert len(recorder._equity_points) == n
        assert len(recorder._timestamps) == n
        assert len(recorder._bars) == n

    def test_no_position_equity_equals_cash(self):
        recorder, acct = _make_recorder(initial_cash=50_000.0)
        acct.get_position.return_value = Position(symbol="AAPL", quantity=0, average_cost=0.0)
        acct.calculate_total_value.return_value = 50_000.0

        bar = _make_bar(close=100.0)
        recorder._on_end_of_bar(EndOfBarEvent(bar))

        assert recorder._equity_points[0] == pytest.approx(50_000.0)

    def test_invalid_bar_skipped(self):
        recorder, acct = _make_recorder()
        bad_bar = _make_bar(close=0.0)
        recorder._on_end_of_bar(EndOfBarEvent(bad_bar))
        assert len(recorder._bars) == 0


# ---------------------------------------------------------------------------
# 6.3 — build_result() with zero trades returns valid BacktestResult
# ---------------------------------------------------------------------------

class TestBuildResult:
    def test_zero_trades_returns_valid_result(self):
        recorder, acct = _make_recorder(initial_cash=100_000.0)
        acct.cash = 100_000.0
        acct.calculate_total_value.return_value = 100_000.0
        acct.get_position.return_value = Position(symbol="AAPL", quantity=0, average_cost=0.0)
        acct._positions = {}

        # Feed some bars to populate equity curve
        for i in range(5):
            bar = _make_bar(close=100.0, ts=datetime(2024, 1, 1) + timedelta(days=i))
            recorder._on_end_of_bar(EndOfBarEvent(bar))

        result = recorder.build_result()

        assert result.trades == []
        assert len(result.equity_curve) == 5
        assert set(result.metrics.keys()) == {"total_return", "max_drawdown", "sharpe_ratio", "win_rate"}

    def test_empty_run_still_builds(self):
        recorder, acct = _make_recorder(initial_cash=100_000.0)
        acct.cash = 100_000.0
        acct._positions = {}
        result = recorder.build_result()
        assert result is not None
        assert result.trades == []
        assert result.equity_curve.empty
