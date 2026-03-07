import unittest
import time
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import FillEvent
from src.trading_system.modules.account_service import AccountService
from src.trading_system.modules.execution_engine import Side

class TestAccountService(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()
        self.engine.start()
        self.service = AccountService(self.engine, initial_cash=10000.0)

    def tearDown(self):
        self.engine.stop()

    def test_initial_balance(self):
        self.assertEqual(self.service.cash, 10000.0)

    def test_has_funds(self):
        self.assertTrue(self.service.has_funds(5000.0))
        self.assertTrue(self.service.has_funds(10000.0))
        self.assertFalse(self.service.has_funds(10001.0))

    def test_fill_updates_cash_and_position(self):
        # Simulate a BUY fill
        fill_data = {
            "order_id": "order_1",
            "symbol": "AAPL",
            "side": Side.BUY,
            "quantity": 10,
            "price": 150.0
        }
        self.engine.put(FillEvent(fill_data))
        
        # Give some time for event processing
        time.sleep(0.5)
        
        # 10 * 150 = 1500. 10000 - 1500 = 8500.
        self.assertEqual(self.service.cash, 8500.0)
        pos = self.service.get_position("AAPL")
        self.assertEqual(pos.quantity, 10)
        self.assertEqual(pos.average_cost, 150.0)

        # Simulate a SELL fill
        fill_data_sell = {
            "order_id": "order_2",
            "symbol": "AAPL",
            "side": Side.SELL,
            "quantity": 5,
            "price": 160.0
        }
        self.engine.put(FillEvent(fill_data_sell))
        time.sleep(0.5)
        
        # 5 * 160 = 800. 8500 + 800 = 9300.
        self.assertEqual(self.service.cash, 9300.0)
        pos = self.service.get_position("AAPL")
        self.assertEqual(pos.quantity, 5)
        self.assertEqual(pos.average_cost, 150.0) # Avg cost remains same on reduction

    def test_insufficient_position(self):
        self.assertFalse(self.service.has_position("MSFT", 1))
        
        # BUY MSFT
        self.engine.put(FillEvent({
            "symbol": "MSFT", "side": Side.BUY, "quantity": 10, "price": 100.0
        }))
        time.sleep(0.5)
        
        self.assertTrue(self.service.has_position("MSFT", 5))
        self.assertTrue(self.service.has_position("MSFT", 10))
        self.assertFalse(self.service.has_position("MSFT", 11))

if __name__ == '__main__':
    unittest.main()
