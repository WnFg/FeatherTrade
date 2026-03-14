import unittest
import time
import uuid
from datetime import datetime
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import MarketEvent
from src.trading_system.modules.backtest_simulator import BacktestSimulator
from src.trading_system.modules.execution_engine import Order, OrderType, Side
from src.trading_system.data.market_data import Tick

class TestBacktestSimulator(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()
        self.engine.start()
        self.simulator = BacktestSimulator(self.engine)

    def tearDown(self):
        self.engine.stop()

    def test_market_order_fill(self):
        """Test if a market order is filled upon receiving a tick."""
        order = Order(
            order_id="test_mkt_1",
            symbol="AAPL",
            order_type=OrderType.MARKET,
            side=Side.BUY,
            quantity=100
        )
        self.simulator.submit_order(order)
        
        # New market data
        tick = Tick("AAPL", datetime.now(), 150.0, 1000)
        self.engine.put(MarketEvent(tick))
        
        time.sleep(0.5)
        
        pos = self.simulator.get_position("AAPL")
        self.assertEqual(pos.quantity, 100)
        self.assertEqual(pos.average_cost, 150.0)

    def test_limit_order_fill(self):
        """Test if a limit order is filled only when the price condition is met."""
        order = Order(
            order_id="test_lmt_1",
            symbol="MSFT",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=50,
            price=200.0
        )
        self.simulator.submit_order(order)
        
        # Price too high, no fill
        self.engine.put(MarketEvent(Tick("MSFT", datetime.now(), 205.0, 1000)))
        time.sleep(0.5)
        self.assertEqual(self.simulator.get_position("MSFT").quantity, 0)

        # Price hits limit
        self.engine.put(MarketEvent(Tick("MSFT", datetime.now(), 199.0, 1000)))
        time.sleep(0.5)
        self.assertEqual(self.simulator.get_position("MSFT").quantity, 50)
        # Fill price is the limit price (200.0), not the market price (199.0)
        self.assertEqual(self.simulator.get_position("MSFT").average_cost, 200.0)

if __name__ == '__main__':
    unittest.main()
