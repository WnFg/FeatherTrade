import unittest
from datetime import datetime
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import SignalEvent
from src.trading_system.modules.backtest_simulator import BacktestSimulator
from src.trading_system.modules.execution_engine import Order, OrderType, Side

class TestStrategyConcurrency(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()
        self.engine.start()
        self.simulator = BacktestSimulator(self.engine)

    def tearDown(self):
        self.engine.stop()

    def test_in_flight_ignoring(self):
        """Verify that multiple signals from same strategy are ignored if one is pending."""
        strategy_id = "test_strat_1"
        
        order1 = Order(
            order_id="order_1",
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=100,
            strategy_id=strategy_id,
            price=140.0 # Price far from current market to keep it pending
        )
        
        # First order should be accepted
        self.simulator.submit_order(order1)
        self.assertTrue(self.simulator.is_in_flight(strategy_id))
        self.assertEqual(len(self.simulator._pending_orders), 1)

        # Second order from same strategy should be ignored
        order2 = Order(
            order_id="order_2",
            symbol="AAPL",
            order_type=OrderType.MARKET,
            side=Side.BUY,
            quantity=50,
            strategy_id=strategy_id
        )
        self.simulator.submit_order(order2)
        # Still only 1 order in pending list
        self.assertEqual(len(self.simulator._pending_orders), 1)

    def test_in_flight_clearing(self):
        """Verify that in-flight status is cleared when order is filled."""
        strategy_id = "test_strat_2"
        
        order = Order(
            order_id="order_3",
            symbol="MSFT",
            order_type=OrderType.MARKET,
            side=Side.BUY,
            quantity=10,
            strategy_id=strategy_id
        )
        
        self.simulator.submit_order(order)
        self.assertTrue(self.simulator.is_in_flight(strategy_id))
        
        # Trigger fill by sending market data
        from src.trading_system.core.event_types import MarketEvent
        from src.trading_system.data.market_data import Tick
        
        tick = Tick("MSFT", datetime.now(), 250.0, 1000)
        self.engine.put(MarketEvent(tick))
        
        import time
        time.sleep(0.5) # Allow event loop to process
        
        # Should not be in flight anymore
        self.assertFalse(self.simulator.is_in_flight(strategy_id))
        self.assertEqual(len(self.simulator._pending_orders), 0)

if __name__ == "__main__":
    unittest.main()
