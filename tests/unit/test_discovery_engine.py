import unittest
import os
import shutil
import tempfile
from src.trading_system.factors.registry import DiscoveryEngine
from src.trading_system.factors.base import BaseFactorLogic, BaseDataSource

class TestDiscoveryEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_discover_logic(self):
        # Create a dummy logic file
        logic_code = """
from src.trading_system.factors.base import BaseFactorLogic
import pandas as pd
from typing import Dict, Any

class CustomLogic(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        return data
"""
        with open(os.path.join(self.test_dir, "custom_logic.py"), "w") as f:
            f.write(logic_code)
            
        discovered = DiscoveryEngine.discover_components(self.test_dir, BaseFactorLogic)
        self.assertIn("customlogic", discovered)
        self.assertTrue(issubclass(discovered["customlogic"], BaseFactorLogic))

    def test_discover_source(self):
        # Create a dummy source file
        source_code = """
from src.trading_system.factors.base import BaseDataSource
import pandas as pd
from datetime import datetime

class CustomSource(BaseDataSource):
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        return pd.DataFrame()
"""
        with open(os.path.join(self.test_dir, "custom_source.py"), "w") as f:
            f.write(source_code)
            
        discovered = DiscoveryEngine.discover_components(self.test_dir, BaseDataSource)
        self.assertIn("customsource", discovered)
        self.assertTrue(issubclass(discovered["customsource"], BaseDataSource))

    def test_ignore_non_subclasses(self):
        # Create a file with a class that does NOT inherit from the base
        code = """
class OtherClass:
    pass
"""
        with open(os.path.join(self.test_dir, "other.py"), "w") as f:
            f.write(code)
            
        discovered = DiscoveryEngine.discover_components(self.test_dir, BaseFactorLogic)
        self.assertEqual(len(discovered), 0)

if __name__ == "__main__":
    unittest.main()
