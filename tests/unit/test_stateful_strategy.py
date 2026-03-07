import unittest
from unittest.mock import MagicMock
from datetime import datetime
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.strategies.stateful_strategy import StatefulStrategy, StrategyState
from src.trading_system.data.market_data import Tick

class MockStatefulStrategy(StatefulStrategy):
    """Concrete implementation for testing purposes."""
    def on_tick_logic(self, tick, context):
        pass
    def on_bar_logic(self, bar, context):
        pass

class TestStatefulStrategy(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock(spec=EventEngine)
        self.params = {
            "strategy_id": "test_stateful",
            "stop_loss_pct": 0.1,  # 10%
            "take_profit_pct": 0.2, # 20%
        }
        self.strategy = MockStatefulStrategy(self.engine, self.params)
        self.mock_context = MagicMock()

    def test_risk_management_stop_loss(self):
        """Verify that stop loss triggers liquidation and state transition."""
        self.strategy.record_entry(price=100.0, qty=50)
        self.strategy.position_qty = 50 # Manually set to simulate held position
        
        # Current price 85 (15% drop, triggers 10% SL)
        tick = Tick("AAPL", datetime.now(), 85.0, 1000)
        
        self.strategy.on_tick(tick, self.mock_context)
        
        self.assertEqual(self.strategy.state, StrategyState.CLOSED)
        # Verify signal sent
        self.engine.put.assert_called_once()
        signal = self.engine.put.call_args[0][0]
        self.assertEqual(signal.data["side"], "SELL")
        self.assertEqual(signal.data["quantity"], 50)

    def test_risk_management_take_profit(self):
        """Verify that take profit triggers liquidation and state transition."""
        self.strategy.record_entry(price=100.0, qty=50)
        self.strategy.position_qty = 50
        
        # Current price 125 (25% gain, triggers 20% TP)
        tick = Tick("AAPL", datetime.now(), 125.0, 1000)
        
        self.strategy.on_tick(tick, self.mock_context)
        
        self.assertEqual(self.strategy.state, StrategyState.CLOSED)
        self.engine.put.assert_called_once()

    def test_closed_state_ignores_events(self):
        """Verify that CLOSED state does not process new ticks."""
        self.strategy.state = StrategyState.CLOSED
        tick = Tick("AAPL", datetime.now(), 100.0, 1000)
        
        # We need to track if on_tick_logic was called
        self.strategy.on_tick_logic = MagicMock()
        self.strategy.on_tick(tick, self.mock_context)
        
        self.strategy.on_tick_logic.assert_not_called()

if __name__ == "__main__":
    unittest.main()
