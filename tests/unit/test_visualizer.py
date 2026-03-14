"""Unit tests for BacktestVisualizer."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.trading_system.backtest.result import BacktestResult, TradeRecord
from src.trading_system.backtest.visualizer import BacktestVisualizer
from src.trading_system.modules.execution_engine import Side


# ---------------------------------------------------------------------------
# Fixture: minimal BacktestResult
# ---------------------------------------------------------------------------

def _make_result() -> BacktestResult:
    from unittest.mock import MagicMock
    timestamps = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    idx = pd.DatetimeIndex(timestamps)

    # Simulated equity: starts at 100_000, grows linearly
    equity_values = [100_000 + i * 500 for i in range(20)]
    equity_curve = pd.Series(equity_values, index=idx, name="equity")

    # Drawdown (flat — no drawdown in linear growth)
    drawdown_curve = pd.Series([0.0] * 20, index=idx, name="drawdown")
    position_curve = pd.Series([0] * 5 + [100] * 10 + [0] * 5, index=idx, name="position")

    trades = [
        TradeRecord(
            timestamp=timestamps[5],
            symbol="AAPL",
            side=Side.BUY,
            quantity=100,
            price=102.5,
            pnl=0.0,
        ),
        TradeRecord(
            timestamp=timestamps[15],
            symbol="AAPL",
            side=Side.SELL,
            quantity=100,
            price=112.0,
            pnl=950.0,
        ),
    ]

    # Minimal bar mocks
    bars = []
    for i, ts in enumerate(timestamps):
        bar = MagicMock()
        bar.timestamp = ts
        bar.close = 100.0 + i * 0.5
        bars.append(bar)

    return BacktestResult(
        symbol="AAPL",
        initial_capital=100_000.0,
        final_cash=90_500.0,
        final_equity=109_500.0,
        trades=trades,
        equity_curve=equity_curve,
        drawdown_curve=drawdown_curve,
        position_curve=position_curve,
        bars=bars,
        metrics={
            "total_return": 0.095,
            "max_drawdown": -0.01,
            "sharpe_ratio": 1.5,
            "win_rate": 1.0,
        },
    )


# ---------------------------------------------------------------------------
# 6.4 — Plotly HTML output
# ---------------------------------------------------------------------------

class TestPlotlyOutput:
    def test_html_file_generated(self):
        pytest.importorskip("plotly")  # skip if plotly not installed
        result = _make_result()
        visualizer = BacktestVisualizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "report.html")
            returned_path = visualizer.plot(result, output_path=out, backend="plotly")
            assert os.path.exists(returned_path), "HTML report file not found"
            assert os.path.getsize(returned_path) > 0, "HTML report file is empty"

    def test_html_contains_symbol(self):
        pytest.importorskip("plotly")
        result = _make_result()
        visualizer = BacktestVisualizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "report.html")
            visualizer.plot(result, output_path=out, backend="plotly")
            with open(out, "r", encoding="utf-8") as f:
                content = f.read()
            assert "AAPL" in content


# ---------------------------------------------------------------------------
# 6.5 — Matplotlib PNG output
# ---------------------------------------------------------------------------

class TestMatplotlibOutput:
    def test_png_file_generated(self):
        pytest.importorskip("matplotlib")  # skip if matplotlib not installed
        result = _make_result()
        visualizer = BacktestVisualizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "report.png")
            returned_path = visualizer.plot(result, output_path=out, backend="matplotlib")
            assert os.path.exists(returned_path), "PNG report file not found"
            assert os.path.getsize(returned_path) > 0, "PNG report file is empty"

    def test_png_with_no_trades(self):
        """Visualizer should not crash when there are no trades."""
        pytest.importorskip("matplotlib")
        result = _make_result()
        result.trades = []
        visualizer = BacktestVisualizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "report_empty.png")
            returned_path = visualizer.plot(result, output_path=out, backend="matplotlib")
            assert os.path.exists(returned_path)
            assert os.path.getsize(returned_path) > 0


# ---------------------------------------------------------------------------
# CSV fallback
# ---------------------------------------------------------------------------

class TestCsvFallback:
    def test_csv_export_creates_files(self):
        result = _make_result()
        visualizer = BacktestVisualizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "report.csv")
            visualizer._export_csv(result, out)
            eq_file = os.path.join(tmpdir, "report_equity.csv")
            tr_file = os.path.join(tmpdir, "report_trades.csv")
            assert os.path.exists(eq_file) and os.path.getsize(eq_file) > 0
            assert os.path.exists(tr_file) and os.path.getsize(tr_file) > 0
