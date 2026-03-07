import unittest
from unittest.mock import MagicMock
from datetime import datetime
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.strategies.atr_trend_strategy import ATRTrendStrategy

class TestATRTrendStrategy(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock(spec=EventEngine)
        self.params = {
            "atr_period": 3,
            "breakout_period": 3,
            "risk_pct": 0.01,
            "atr_multiplier": 2.0,
            "max_equity_pct": 0.05
        }
        self.strategy = ATRTrendStrategy(self.engine, self.params)
        self.mock_context = MagicMock()

    def test_indicator_calculations(self):
        """Verify ATR and Breakout High calculations."""
        bars = [
            Bar("AAPL", datetime.now(), 100, 110, 90, 105, 1000), # TR: 20
            Bar("AAPL", datetime.now(), 105, 115, 100, 110, 1000), # TR: 15 (115-100)
            Bar("AAPL", datetime.now(), 110, 120, 105, 115, 1000), # TR: 15 (120-105)
            Bar("AAPL", datetime.now(), 115, 125, 110, 120, 1000)  # Current
        ]
        
        for b in bars:
            self.strategy.on_bar_logic(b, self.mock_context)
            
        # Breakout High of previous 3 bars (110, 115, 120) -> 120
        self.assertEqual(self.strategy._calculate_breakout_high(), 120.0)
        
        # ATR of previous 3 TRs (15, 15, 15) -> 45 / 3 = 15.0
        self.assertEqual(self.strategy._calculate_atr(), 15.0)

    def test_unit_sizing_and_cap(self):
        """Verify 1 UNIT calculation and 5% position cap."""
        # Scenario 1: Risk based sizing (1% risk)
        # Equity: 100,000 -> Risk: 1,000
        # Price: 150, ATR: 2.5, Multiplier: 2 -> Stop distance: 5.0
        # Qty: 1,000 / 5.0 = 200 units
        # Value: 200 * 150 = 30,000 (30% of equity)
        # Cap: 5% of 100,000 = 5,000 / 150 = 33.33 -> 33 units
        
        qty = self.strategy._calculate_unit_size(150.0, 2.5, 100000.0)
        self.assertEqual(qty, 33) # Limited by 5% cap (33*150=4950 < 5000)

        # Scenario 2: Risk based sizing (not capped)
        # Equity: 1,000,000 -> Risk: 10,000
        # Price: 150, ATR: 2.5, Multiplier: 2 -> Stop distance: 5.0
        # Qty: 10,000 / 5.0 = 2000 units
        # Value: 2000 * 150 = 300,000 (30% of equity - still high?)
        # Cap: 5% of 1,000,000 = 50,000 / 150 = 333 units
        qty2 = self.strategy._calculate_unit_size(150.0, 2.5, 1000000.0)
        self.assertEqual(qty2, 333)

if __name__ == "__main__":
    unittest.main()
