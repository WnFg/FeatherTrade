import unittest
import os
import sqlite3
from datetime import datetime
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.models import FactorDefinition, FactorValue
from src.trading_system.factors.service import FactorService, MovingAverageFactor, FileDataSource

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
        self.service.register_source("csv_file", FileDataSource("/Users/wfang/project/pycharm/tradeSystem/factor_test_data.csv"))
        
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

    def test_category_query(self):
        # 3.2 & 6.2
        defn1 = FactorDefinition(
            id=None, name="f1", display_name="F1", category="Momentum", 
            description="D1", formula_config={}
        )
        defn2 = FactorDefinition(
            id=None, name="f2", display_name="F2", category="Volatility", 
            description="D2", formula_config={}
        )
        self.service.registry.register_factor(defn1)
        self.service.registry.register_factor(defn2)
        
        momentum_factors = self.service.registry.list_factors("Momentum")
        self.assertEqual(len(momentum_factors), 1)
        self.assertEqual(momentum_factors[0].name, "f1")
        
        all_factors = self.service.registry.list_factors()
        self.assertEqual(len(all_factors), 2)

    def test_caching_layer(self):
        # 6.3
        defn = FactorDefinition(
            id=None, name="c1", display_name="C1", category="C", 
            description="D", formula_config={}
        )
        fid = self.service.registry.register_factor(defn)
        
        val = FactorValue(id=None, factor_id=fid, symbol="AAPL", timestamp=datetime.now(), value=1.0)
        self.db.insert_factor_values([val])
        
        # First call - database
        values1 = self.service.get_factor_values("AAPL", "c1")
        self.assertEqual(len(values1), 1)
        
        # Modify database directly (bypass service)
        val2 = FactorValue(id=None, factor_id=fid, symbol="AAPL", timestamp=datetime.now(), value=2.0)
        self.db.insert_factor_values([val2])
        
        # Second call - should return cached values (still 1)
        values2 = self.service.get_factor_values("AAPL", "c1")
        self.assertEqual(len(values2), 1)
        self.assertEqual(values2[0].value, 1.0)
        
        # Clear cache and call again - should return 2 values
        self.service.clear_cache()
        values3 = self.service.get_factor_values("AAPL", "c1")
        self.assertEqual(len(values3), 2)

if __name__ == "__main__":
    unittest.main()
