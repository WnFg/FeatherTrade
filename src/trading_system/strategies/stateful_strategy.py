from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.data.market_data import Bar, Tick
from .base_strategy import BaseStrategy
from .context import StrategyContext

class StrategyState(Enum):
    NORMAL = "NORMAL"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"

class StatefulStrategy(BaseStrategy):
    """
    Advanced strategy base class with state machine and risk management logic.
    """
    def __init__(self, event_engine: EventEngine, params: Dict[str, Any] = None):
        super().__init__(event_engine, params)
        self.state = StrategyState.NORMAL
        
        # Risk management parameters
        self.stop_loss_pct = self._params.get("stop_loss_pct", 0.0)
        self.take_profit_pct = self._params.get("take_profit_pct", 0.0)
        self.max_position = self._params.get("max_position", 100)
        
        # Track entry price for SL/TP
        self.entry_price = 0.0
        self.position_qty = 0

    def on_tick(self, tick: Tick, context: StrategyContext):
        if self.state == StrategyState.CLOSED:
            return
            
        if self.state == StrategyState.CLOSING:
            self._handle_closing(tick)
            return
            
        # Normal state: check risk then signal
        if self.position_qty != 0:
            if self.check_risk(tick, context):
                self.state = StrategyState.CLOSING
                self._handle_closing(tick)
                return
        
        self.on_tick_logic(tick, context)

    def on_bar(self, bar: Bar, context: StrategyContext):
        if self.state == StrategyState.CLOSED:
            return
        
        if self.state == StrategyState.CLOSING:
            self._handle_closing(bar)
            return
            
        # Normal state: check risk then signal
        if self.position_qty != 0:
            if self.check_risk(bar, context):
                self.state = StrategyState.CLOSING
                self._handle_closing(bar)
                return

        self.on_bar_logic(bar, context)

    @abstractmethod
    def check_risk(self, data: Any, context: StrategyContext) -> bool:
        pass

    def _handle_closing(self, data: Any):
        """Sends a signal to close all positions."""
        if self.position_qty > 0:
            self.send_signal(data.symbol, "SELL", self.position_qty, 0.0)
            # In a real system, we'd wait for fill event to move to CLOSED
            # For this MVP, we move to CLOSED immediately after signal
            self.state = StrategyState.CLOSED
            print(f"Strategy {self.strategy_id}: Sent liquidation signal for {self.position_qty}")

    @abstractmethod
    def on_tick_logic(self, tick: Tick, context: StrategyContext):
        pass

    @abstractmethod
    def on_bar_logic(self, bar: Bar, context: StrategyContext):
        pass

    def record_entry(self, price: float, qty: int):
        """Helper to record entry for risk tracking."""
        self.entry_price = price
        self.position_qty = qty
