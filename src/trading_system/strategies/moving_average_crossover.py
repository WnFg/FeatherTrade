from typing import Any, Dict, List
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.strategies.stateful_strategy import StatefulStrategy, StrategyContext
from src.trading_system.data.market_data import Bar, Tick

class MovingAverageCrossover(StatefulStrategy):
    """
    A simple Moving Average Crossover strategy as a reference implementation.
    Logic: BUY when fast SMA > slow SMA, SELL when fast SMA < slow SMA.
    """
    def __init__(self, event_engine: EventEngine, params: Dict[str, Any] = None):
        super().__init__(event_engine, params)
        self._fast_period = self._params.get("fast_period", 5)
        self._slow_period = self._params.get("slow_period", 20)
        self._quantity = self._params.get("quantity", 100)
        
        self._prices: Dict[str, List[float]] = {}

    def on_tick_logic(self, tick: Tick, context: StrategyContext):
        """Ticks are ignored for SMA crossover."""
        pass

    def on_bar_logic(self, bar: Bar, context: StrategyContext):
        """Processes a new bar and generates signals based on SMA crossover."""
        symbol = bar.symbol
        if symbol not in self._prices:
            self._prices[symbol] = []
            
        self._prices[symbol].append(bar.close)
        
        # We need at least 'slow_period' bars to calculate SMA
        if len(self._prices[symbol]) < self._slow_period + 1:
            return
            
        fast_sma_current = self._calculate_sma(self._prices[symbol], self._fast_period)
        slow_sma_current = self._calculate_sma(self._prices[symbol], self._slow_period)
        
        fast_sma_prev = self._calculate_sma(self._prices[symbol][:-1], self._fast_period)
        slow_sma_prev = self._calculate_sma(self._prices[symbol][:-1], self._slow_period)
        
        # Crossover logic
        if fast_sma_prev <= slow_sma_prev and fast_sma_current > slow_sma_current:
            if self.position_qty == 0:
                self.send_signal(symbol, "BUY", self._quantity)
                self.record_entry(bar.close, self._quantity)
        
        elif fast_sma_prev >= slow_sma_prev and fast_sma_current < slow_sma_current:
            if self.position_qty > 0:
                self.send_signal(symbol, "SELL", self.position_qty)
                self.record_entry(0.0, 0)

    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Helper to calculate Simple Moving Average."""
        subset = prices[-period:]
        return sum(subset) / len(subset)

    def check_risk(self, data: Any, context: StrategyContext) -> bool:
        """No additional risk checks for this strategy — always proceed."""
        return True
