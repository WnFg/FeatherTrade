import unittest
from unittest.mock import MagicMock
from src.trading_system.strategies.context import StrategyContext

class TestStrategyContext(unittest.TestCase):
    def setUp(self):
        self.mock_account = MagicMock()
        self.mock_execution = MagicMock()
        self.mock_factors = MagicMock()
        self.context = StrategyContext(
            strategy_id="test_strat",
            account_service=self.mock_account,
            execution_engine=self.mock_execution,
            factor_service=self.mock_factors
        )

    def test_service_access(self):
        """Verify that services are correctly wrapped and accessible."""
        self.assertEqual(self.context.account, self.mock_account)
        self.assertEqual(self.context.execution, self.mock_execution)
        self.assertEqual(self.context.factors, self.mock_factors)

    def test_kv_store(self):
        """Verify memory KV store functionality."""
        self.context.state.set("key1", "value1")
        self.assertEqual(self.context.state.get("key1"), "value1")
        
        self.context.state.set("key2", 123.45)
        self.assertEqual(self.context.state.get("key2"), 123.45)
        
        # Test default value
        self.assertEqual(self.context.state.get("non_existent", "default"), "default")
        
        # Test clear
        self.context.state.clear()
        self.assertIsNone(self.context.state.get("key1"))

if __name__ == "__main__":
    unittest.main()
