import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime
from src.trading_system.factors.builtin.data_sources import TuShareDataSource


class TestTuShareDataSource(unittest.TestCase):
    def setUp(self):
        self.token = "fake_token"

    def test_no_arg_constructor(self):
        """Test TuShareDataSource can be instantiated without arguments."""
        source = TuShareDataSource()
        self.assertIsNone(source.pro)
        self.assertEqual(source.api, 'daily')

    def test_fetch_data_without_configure_raises(self):
        """Test fetch_data raises error if not configured."""
        source = TuShareDataSource()
        with self.assertRaises(RuntimeError):
            source.fetch_data('000001.SZ', datetime(2024, 1, 1), datetime(2024, 1, 10))

    @patch.dict('os.environ', {}, clear=True)
    def test_configure_missing_token_raises(self):
        """Test configure raises error when TUSHARE_TOKEN is not set."""
        source = TuShareDataSource()
        with self.assertRaises(ValueError):
            source.configure({})

    @patch('tushare.pro.client')
    @patch('tushare.pro_api')
    def test_fetch_daily_data(self, mock_pro_api, mock_client):
        # Setup mock pro_api and its daily method
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro

        # Mock data returned by TuShare
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ', '000001.SZ'],
            'trade_date': ['20230101', '20230102'],
            'close': [10.5, 11.0],
            'vol': [1000, 1500]
        })
        mock_pro.daily.return_value = mock_df

        source = TuShareDataSource()
        source.configure({'token': self.token, 'api': 'daily'})
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)

        df = source.fetch_data('000001.SZ', start_date, end_date)

        # Verify TuShare daily was called with correct params
        mock_pro.daily.assert_called_once_with(
            ts_code='000001.SZ',
            start_date='20230101',
            end_date='20230102'
        )

        # Verify DataFrame mapping
        self.assertIn('symbol', df.columns)
        self.assertIn('timestamp', df.columns)
        self.assertIn('volume', df.columns)
        self.assertEqual(df.iloc[0]['symbol'], '000001.SZ')
        self.assertEqual(df.iloc[0]['timestamp'], pd.to_datetime('2023-01-01'))
        self.assertEqual(df.iloc[0]['volume'], 1000)

    @patch('tushare.pro.client')
    @patch('tushare.pro_api')
    def test_custom_params_daily_basic(self, mock_pro_api, mock_client):
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro

        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20230101'],
            'pe': [8.5],
            'pb': [1.2],
        })
        mock_pro.daily_basic.return_value = mock_df

        source = TuShareDataSource()
        source.configure({
            'token': self.token,
            'api': 'daily_basic',
            'fields': ['ts_code', 'trade_date', 'pe', 'pb']
        })

        df = source.fetch_data('000001.SZ', datetime(2023, 1, 1), datetime(2023, 1, 1))

        mock_pro.daily_basic.assert_called_once_with(
            ts_code='000001.SZ',
            start_date='20230101',
            end_date='20230101',
            fields='ts_code,trade_date,pe,pb'
        )
        self.assertIn('pe', df.columns)
        self.assertIn('pb', df.columns)

    @patch('tushare.pro.client')
    @patch('tushare.pro_api')
    def test_fetch_empty_result(self, mock_pro_api, mock_client):
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        mock_pro.daily.return_value = pd.DataFrame()

        source = TuShareDataSource()
        source.configure({'token': self.token, 'api': 'daily'})

        result = source.fetch_data('000001.SZ', datetime(2024, 1, 1), datetime(2024, 1, 10))
        self.assertTrue(result.empty)

    @patch('tushare.pro.client')
    @patch('tushare.pro_api')
    def test_date_format_conversion(self, mock_pro_api, mock_client):
        """Test YYYYMMDD to datetime conversion."""
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro

        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20240315'],
            'close': [10.0],
        })
        mock_pro.daily.return_value = mock_df

        source = TuShareDataSource()
        source.configure({'token': self.token, 'api': 'daily'})

        result = source.fetch_data('000001.SZ', datetime(2024, 3, 1), datetime(2024, 3, 31))
        self.assertEqual(result['timestamp'].iloc[0], pd.Timestamp('2024-03-15'))


if __name__ == '__main__':
    unittest.main()
