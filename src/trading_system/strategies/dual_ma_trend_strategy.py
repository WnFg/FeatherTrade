"""
DualMATrendStrategy: dual moving-average trend-following strategy.

Logic:
- Fast MA crosses above Slow MA  → BUY (trend start)
- Fast MA crosses below Slow MA  → SELL (exit long)
- Optional trend filter: only enter when close > long_ma (medium-term uptrend)
- Position sizing: fixed fraction of equity

Default parameters (tuned for A-share daily bars):
    fast_period  = 10   (10-day MA)
    slow_period  = 30   (30-day MA)
    trend_period = 60   (60-day MA, trend filter)
    equity_pct   = 0.95 (use 95% of cash for entry)
"""
from collections import deque
from typing import Any, Dict, List

from src.trading_system.core.event_engine import EventEngine
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.strategies.stateful_strategy import StatefulStrategy, StrategyContext, StrategyState


class DualMATrendStrategy(StatefulStrategy):
    """
    Dual Moving-Average cross-over trend strategy for daily bar data.

    Entry : fast_ma crosses above slow_ma AND close > trend_ma
    Exit  : fast_ma crosses below slow_ma  OR  ATR stop-loss triggered
    """

    def __init__(self, event_engine: EventEngine, params: Dict[str, Any] = None):
        super().__init__(event_engine, params)
        self._fast_period  = self._params.get("fast_period",  10)
        self._slow_period  = self._params.get("slow_period",  30)
        self._trend_period = self._params.get("trend_period", 60)
        self._equity_pct   = self._params.get("equity_pct",  0.95)
        self._atr_stop_mult = self._params.get("atr_stop_mult", 2.0)  # ATR multiplier for stop
        self._atr_period   = self._params.get("atr_period",   14)

        max_buf = self._trend_period + self._atr_period + 2
        self._bars: deque = deque(maxlen=max_buf)

        self._prev_fast_above: bool = False   # golden-cross state tracker
        self._stop_price: float = 0.0

    # ------------------------------------------------------------------ #
    #  StatefulStrategy hooks
    # ------------------------------------------------------------------ #

    def on_tick_logic(self, tick: Tick, context: StrategyContext):
        pass  # strategy operates on daily bars only

    def on_bar_logic(self, bar: Bar, context: StrategyContext):
        self._bars.append(bar)

        fast_ma  = self._sma(self._fast_period)
        slow_ma  = self._sma(self._slow_period)
        trend_ma = self._sma(self._trend_period)

        if fast_ma is None or slow_ma is None:
            return  # not enough data yet

        fast_above_now = fast_ma > slow_ma

        # True if we have an actual filled position OR a pending buy in-flight
        in_position = self.position_qty > 0 or self._pending_buy_qty > 0

        # ── Exit signal ──────────────────────────────────────────────────
        if in_position and not fast_above_now and self._prev_fast_above:
            sell_qty = self.position_qty or self._pending_buy_qty
            print(f"{self.strategy_id}: MA Death Cross @ {bar.close:.2f} — exit long ({sell_qty} shares)")
            self.send_signal(bar.symbol, "SELL", sell_qty, bar.close)
            self._stop_price = 0.0

        # ── Entry signal ─────────────────────────────────────────────────
        elif not in_position and fast_above_now and not self._prev_fast_above:
            # Trend filter: only enter if price is above long MA
            if trend_ma is not None and bar.close < trend_ma:
                pass  # against medium-term trend, skip
            else:
                qty = self._calc_qty(bar.close, context)
                if qty > 0:
                    atr = self._atr()
                    self._stop_price = bar.close - self._atr_stop_mult * atr if atr else bar.close * 0.95
                    print(f"{self.strategy_id}: MA Golden Cross @ {bar.close:.2f} — buy {qty} shares, stop={self._stop_price:.2f}")
                    self.send_signal(bar.symbol, "BUY", qty, bar.close)
                    self.record_entry(bar.close, qty)

        self._prev_fast_above = fast_above_now

    def check_risk(self, data: Any, context: StrategyContext) -> bool:
        """ATR-based trailing stop."""
        if (self.position_qty > 0 or self._pending_buy_qty > 0) and self._stop_price > 0:
            price = data.close if hasattr(data, "close") else data.price
            if price <= self._stop_price:
                print(f"{self.strategy_id}: Stop loss hit @ {price:.2f} (stop={self._stop_price:.2f})")
                return True
        return False

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _sma(self, period: int):
        if len(self._bars) < period:
            return None
        recent = list(self._bars)[-period:]
        return sum(b.close for b in recent) / period

    def _atr(self) -> float:
        bars = list(self._bars)
        if len(bars) < self._atr_period + 1:
            return 0.0
        trs = []
        for i in range(1, len(bars)):
            tr = max(
                bars[i].high - bars[i].low,
                abs(bars[i].high - bars[i - 1].close),
                abs(bars[i].low  - bars[i - 1].close),
            )
            trs.append(tr)
        return sum(trs[-self._atr_period:]) / self._atr_period

    def _calc_qty(self, price: float, context: StrategyContext) -> int:
        cash = context.account.cash
        if cash <= 0 or price <= 0:
            return 0
        # A-shares must be bought in multiples of 100 (1 手)
        raw = int(cash * self._equity_pct / price)
        return max(0, raw - (raw % 100))
