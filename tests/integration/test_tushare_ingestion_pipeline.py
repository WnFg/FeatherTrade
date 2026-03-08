import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import os
from datetime import datetime
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.service import FactorService, TuShareDataSource, MovingAverageFactor
from src.trading_system.factors.models import FactorDefinition

class TestTuShareIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_tushare_ingestion.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = FactorDatabase(self.db_path)
        self.service = FactorService(self.db)
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('tushare.pro_api')
    def test_full_pipeline(self, mock_pro_api):
        # 1. Setup Mock TuShare
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        
        # 10 days of data
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ'] * 10,
            'trade_date': [f'202301{i+1:02d}' for i in range(10)],
            'close': [float(100 + i) for i in range(10)]
        })
        mock_pro.daily.return_value = mock_df
        
        # 2. Register Factor and Logic
        defn = FactorDefinition(
            id=None,
            name="sma_5",
            display_name="SMA 5",
            category="Trend",
            description="5-day Simple Moving Average",
            formula_config={"window": 5, "price_key": "close"}
        )
        self.service.registry.register_factor(defn)
        self.service.register_logic("sma_5", MovingAverageFactor())
        
        # 3. Register TuShare Source
        source = TuShareDataSource(token="fake", api_name="daily")
        self.service.register_source("tushare_daily", source)
        
        # 4. Run Ingestion
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 10)
        self.service.compute_and_store("000001.SZ", "sma_5", "tushare_daily", start, end)
        
        # 5. Verify Database
        values = self.db.query_factor_values("sma_5", "000001.SZ")
        
        # With window=5 and 10 days of data, we should have 10 - 5 + 1 = 6 values
        self.assertEqual(len(values), 6)
        
        # Latest value (Day 10): (105+106+107+108+109)/5 = 107.0
        # Wait, close values are 100, 101, 102, 103, 104, 105, 106, 107, 108, 109
        # Last 5: 105, 106, 107, 108, 109. Sum = 535. Avg = 107.0
        self.assertEqual(values[0].value, 107.0)
        
        # First value (Day 5): (100+101+102+103+104)/5 = 102.0
        self.assertEqual(values[-1].value, 102.0)

if __name__ == '__main__':
    unittest.main()
