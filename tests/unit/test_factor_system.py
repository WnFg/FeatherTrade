import unittest
import os
import sqlite3
from datetime import datetime
from trading_system.data.factor_database import FactorDatabase
from trading_system.data.factor_models import FactorDefinition, FactorValue
from trading_system.modules.factor_service import FactorService, MovingAverageFactor, FileDataSource

class TestFactorSystem(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_factors.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = FactorDatabase(self.db_path)
        self.service = FactorService(self.db)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists("factor_test_data.csv"):
            pass # Keep it for other tests or cleanup if needed

    def test_factor_registration(self):
        # 3.1 & 3.2
        defn = FactorDefinition(
            id=None,
            name="sma_3",
            display_name="SMA (3)",
            category="Momentum",
            description="Simple Moving Average with window 3",
            formula_config={"window": 3, "price_key": "price"}
        )
        fid = self.service.registry.register_factor(defn)
        self.assertIsNotNone(fid)
        
        retrieved = self.service.registry.get_factor("sma_3")
        self.assertEqual(retrieved.name, "sma_3")
        self.assertEqual(retrieved.formula_config["window"], 3)

    def test_factor_computation_and_storage(self):
        # 5.1, 5.2, 4.1
        defn = FactorDefinition(
            id=None,
            name="sma_3",
            display_name="SMA (3)",
            category="Momentum",
            description="Simple Moving Average with window 3",
            formula_config={"window": 3, "price_key": "price"}
        )
        self.service.registry.register_factor(defn)
        
        self.service.register_logic("sma_3", MovingAverageFactor())
        self.service.register_source("csv_file", FileDataSource("factor_test_data.csv"))
        
        start = datetime.fromisoformat("2023-01-01T10:00:00")
        end = datetime.fromisoformat("2023-01-01T10:04:00")
        
        self.service.compute_and_store("AAPL", "sma_3", "csv_file", start, end)
        
        # 6.1
        values = self.service.get_factor_values("AAPL", "sma_3")
        self.assertEqual(len(values), 3) # 5 points, window 3 -> points at index 2, 3, 4
        
        # Latest value should be at index 4: (152 + 153 + 154) / 3 = 153.0
        self.assertEqual(values[0].value, 153.0) 
        # First computed value should be at index 2: (150 + 151 + 152) / 3 = 151.0
        self.assertEqual(values[-1].value, 151.0)

if __name__ == "__main__":
    unittest.main()
