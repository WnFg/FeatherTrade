import unittest
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.modules.account_service import AccountService
from src.trading_system.modules.execution_engine import Position
from src.trading_system.risk.fixed_stop_loss import FixedStopLossStrategy
from src.trading_system.risk.risk_manager import RiskManager

class TestFixedStopLossStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = FixedStopLossStrategy({"stop_loss_pct": 0.05})
        
    def test_no_position(self):
        pos = Position("AAPL", 0, 0.0)
        self.assertIsNone(self.strategy.evaluate(pos, 100.0))

    def test_long_position_no_stop(self):
        pos = Position("AAPL", 100, 100.0)
        self.assertIsNone(self.strategy.evaluate(pos, 96.0)) # 4% drop
        self.assertIsNone(self.strategy.evaluate(pos, 110.0)) # Profit
        
    def test_long_position_stop_triggered(self):
        pos = Position("AAPL", 100, 100.0)
        self.assertEqual(self.strategy.evaluate(pos, 95.0), "STOP_LOSS") # 5% drop
        self.assertEqual(self.strategy.evaluate(pos, 90.0), "STOP_LOSS") # 10% drop

    def test_short_position_stop_triggered(self):
        pos = Position("AAPL", -100, 100.0)
        self.assertIsNone(self.strategy.evaluate(pos, 104.0)) # 4% rise (loss)
        self.assertEqual(self.strategy.evaluate(pos, 105.0), "STOP_LOSS") # 5% rise (loss)

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()
        self.engine.start()
        self.account_service = AccountService(self.engine)
        self.manager = RiskManager(self.engine, self.account_service)

    def tearDown(self):
        self.engine.stop()

    def test_trigger_risk_signal(self):
        # We manually inject a position into the account service for testing
        self.account_service._positions["AAPL"] = Position("AAPL", 100, 100.0)
        
        received_signals = []
        def handler(event):
            received_signals.append(event)
            
        self.engine.register("risk_signal", handler)
        
        self.manager._trigger_risk_signal("AAPL", self.account_service.get_position("AAPL"), "TEST_ACTION")
        
        import time
        time.sleep(0.5)
        
        self.assertEqual(len(received_signals), 1)
        signal = received_signals[0].data
        self.assertEqual(signal["symbol"], "AAPL")
        self.assertEqual(signal["side"], "SELL")
        self.assertEqual(signal["quantity"], 100)
        self.assertEqual(signal["action_type"], "TEST_ACTION")

if __name__ == '__main__':
    unittest.main()
