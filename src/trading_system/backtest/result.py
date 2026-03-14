from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.trading_system.modules.execution_engine import Side


@dataclass
class TradeRecord:
    """Represents a single fill/trade during a backtest."""
    timestamp: datetime
    symbol: str
    side: Side
    quantity: int
    price: float
    pnl: float = 0.0  # Realised P&L; only meaningful for SELL fills


@dataclass
class BacktestResult:
    """Structured result object produced by BacktestRecorder.build_result()."""
    symbol: str
    initial_capital: float
    final_cash: float
    final_equity: float
    trades: List[TradeRecord] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    drawdown_curve: pd.Series = field(default_factory=pd.Series)
    position_curve: pd.Series = field(default_factory=pd.Series)
    bars: list = field(default_factory=list)  # List[Bar]
    metrics: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def compute_drawdown_curve(equity_curve: pd.Series) -> pd.Series:
    """Return a Series of drawdown values (negative percentages) from the equity curve."""
    if equity_curve.empty:
        return pd.Series(dtype=float)
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    return drawdown


def compute_metrics(
    equity_curve: pd.Series,
    trades: List[TradeRecord],
    initial_capital: float,
) -> Dict[str, float]:
    """Calculate key performance metrics from equity curve and trade list."""
    metrics: Dict[str, float] = {}

    # Total return
    if initial_capital > 0 and not equity_curve.empty:
        metrics["total_return"] = (equity_curve.iloc[-1] - initial_capital) / initial_capital
    else:
        metrics["total_return"] = 0.0

    # Max drawdown
    dd = compute_drawdown_curve(equity_curve)
    metrics["max_drawdown"] = float(dd.min()) if not dd.empty else 0.0

    # Sharpe ratio (annualised, assumes daily bars, risk-free = 0)
    if len(equity_curve) > 1:
        daily_returns = equity_curve.pct_change().dropna()
        std = daily_returns.std()
        if std > 0:
            metrics["sharpe_ratio"] = float(daily_returns.mean() / std * np.sqrt(252))
        else:
            metrics["sharpe_ratio"] = 0.0
    else:
        metrics["sharpe_ratio"] = 0.0

    # Win rate (percentage of SELL trades with pnl > 0)
    sell_trades = [t for t in trades if t.side == Side.SELL]
    if sell_trades:
        winning = sum(1 for t in sell_trades if t.pnl > 0)
        metrics["win_rate"] = winning / len(sell_trades)
    else:
        metrics["win_rate"] = 0.0

    return metrics
