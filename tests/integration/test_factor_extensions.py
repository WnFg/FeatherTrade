import unittest
import os
from datetime import datetime
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.models import FactorDefinition
from src.trading_system.factors.service import FactorService

class TestFactorExtensions(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_ext_factors.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = FactorDatabase(self.db_path)
        # Use default paths (src/trading_system/factors/builtin and src/trading_system/factors/extensions)
        self.service = FactorService(self.db)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_extension_discovery(self):
        # Check if extension classes are found by namespaced names
        logic_cls = self.service.registry.get_logic_class("extensions.extensionlogic")
        self.assertIsNotNone(logic_cls)

        source_cls = self.service.registry.get_source_class("extensions.extensionsource")
        self.assertIsNotNone(source_cls)

        # Check if they are found by simple names (precedence: user extensions)
        logic_cls_simple = self.service.registry.get_logic_class("extensionlogic")
        self.assertEqual(logic_cls, logic_cls_simple)

    def test_config_scanning(self):
        """Verify that config scanning discovers FACTOR_CONFIGS, DATA_SOURCE_CONFIGS, SCHEDULE_CONFIGS."""
        # Check if example_value_factors configs were discovered
        pe_factor = self.service.db.get_factor_definition("pe_ratio")
        if pe_factor:  # Only test if example extension exists
            self.assertEqual(pe_factor["category"], "value")

            # Check data source config
            ds_config = self.service.registry.get_data_source_config("tushare_daily_basic")
            self.assertIsNotNone(ds_config)
            self.assertEqual(ds_config.source_class, "TuShareDataSource")

            # Check schedule config
            schedule_config = self.service.registry.get_schedule_config("daily_value_factors")
            self.assertIsNotNone(schedule_config)
            self.assertEqual(schedule_config.factor, "pe_ratio")

    def test_extension_pipeline(self):
        # 1. Register factor that uses extension logic
        # Name MUST match the logic class name (lowercase) for automatic discovery
        defn = FactorDefinition(
            id=None,
            name="extensionlogic",
            display_name="Extension Factor",
            category="Test",
            description="Uses extension logic",
            formula_config={"multiplier": 2.0}
        )
        self.service.registry.register_factor(defn)
        
        # 2. Run compute_and_store using extension source and logic
        start = datetime.now()
        end = datetime.now()
        
        # This will internally call self._get_source("extensionsource") and self._get_logic("extensionlogic")
        self.service.compute_and_store("TEST", "extensionlogic", "extensionsource", start, end)
        
        # 3. Verify results in DB
        values = self.service.get_factor_values("TEST", "extensionlogic")
        self.assertEqual(len(values), 2)
        # Price 10.0 * multiplier 2.0 = 20.0
        self.assertEqual(values[-1].value, 20.0) 
        # Price 20.0 * multiplier 2.0 = 40.0
        self.assertEqual(values[0].value, 40.0)

if __name__ == "__main__":
    unittest.main()
