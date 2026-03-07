from typing import Any, Dict, List
import math
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.strategies.stateful_strategy import StatefulStrategy, StrategyContext, StrategyState

class ATRTrendStrategy(StatefulStrategy):
    """
    Trend-following strategy using ATR for volatility-based risk management
    and position sizing.
    """
    def __init__(self, event_engine: EventEngine, params: Dict[str, Any] = None):
        super().__init__(event_engine, params)
        
        # Configuration
        self._atr_period = self._params.get("atr_period", 14)
        self._breakout_period = self._params.get("breakout_period", 20)
        self._risk_pct = self._params.get("risk_pct", 0.01)  # 1% risk per unit
        self._atr_multiplier = self._params.get("atr_multiplier", 2.0)
        self._max_equity_pct = self._params.get("max_equity_pct", 0.05) # 5% max position
        
        # State
        self._bars: List[Bar] = []
        self._stop_loss_price = 0.0

    def on_tick_logic(self, tick: Tick, context: StrategyContext):
        """Ticks are not used for indicator calculation in this strategy."""
        pass

    def on_bar_logic(self, bar: Bar, context: StrategyContext):
        """Processes bars to update indicators and check entry conditions."""
        self._bars.append(bar)
        
        # Keep only what we need for calculations
        max_needed = max(self._atr_period + 1, self._breakout_period + 1)
        if len(self._bars) > max_needed + 1:
            self._bars.pop(0)
            
        if self.state != StrategyState.NORMAL or self.position_qty > 0:
            return
            
        # Entry logic
        breakout_high = self._calculate_breakout_high()
        if bar.close > breakout_high:
            atr = self._calculate_atr()
            if atr <= 0:
                return
                
            # Get account balance from context
            balance = context.account.cash
            
            qty = self._calculate_unit_size(bar.close, atr, balance)
            if qty > 0:
                print(f"ATRTrendStrategy: Breakout detected! Price {bar.close} > {breakout_high}")
                self._stop_loss_price = bar.close - (self._atr_multiplier * atr)
                self.send_signal(bar.symbol, "BUY", qty, bar.close)
                self.record_entry(bar.close, qty)
                print(f"ATRTrendStrategy: Set Stop Loss at {self._stop_loss_price}")

    def check_risk(self, data: Any, context: StrategyContext) -> bool:
        """Volatility-based Stop Loss check."""
        if self.position_qty > 0 and self._stop_loss_price > 0:
            price = data.price if hasattr(data, 'price') else data.close
            if price <= self._stop_loss_price:
                print(f"ATRTrendStrategy: ATR Stop Loss triggered at {price} (SL: {self._stop_loss_price})")
                return True
        return False

    def _calculate_atr(self) -> float:
        """
        Calculates Average True Range.
        Formula: Simple moving average of TR for the first period.
        """
        if len(self._bars) < self._atr_period + 1:
            return 0.0
            
        trs = []
        for i in range(1, len(self._bars)):
            high = self._bars[i].high
            low = self._bars[i].low
            prev_close = self._bars[i-1].close
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            trs.append(tr)
            
        relevant_trs = trs[-self._atr_period:]
        return sum(relevant_trs) / self._atr_period

    def _calculate_breakout_high(self) -> float:
        """Calculates N-period high (excluding current bar)."""
        if len(self._bars) < self._breakout_period + 1:
            return float('inf') # Not enough data
            
        # Look at previous N bars
        lookback_bars = self._bars[-(self._breakout_period + 1):-1]
        return max(b.high for b in lookback_bars)

    def _calculate_unit_size(self, current_price: float, atr: float, total_equity: float) -> int:
        """
        Calculates 1 UNIT quantity based on ATR risk and 5% cap.
        Formula: Quantity = (Total Equity * Risk %) / (ATR * Multiplier)
        """
        if atr <= 0 or current_price <= 0:
            return 0
            
        stop_distance = self._atr_multiplier * atr
        risk_amount = total_equity * self._risk_pct
        
        # 1 UNIT based on risk
        unit_qty = int(risk_amount / stop_distance)
        
        # 5% Max position limit
        max_position_value = total_equity * self._max_equity_pct
        max_qty = int(max_position_value / current_price)
        
        final_qty = min(unit_qty, max_qty)
        return max(0, final_qty)
