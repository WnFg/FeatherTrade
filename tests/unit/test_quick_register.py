import pytest
import pandas as pd
from datetime import datetime
from src.trading_system.factors.quick_register import (
    QuickRegisterConfig, ColumnExtractLogic, detect_factor_columns
)


class TestColumnExtractLogic:
    def _make_df(self, **kwargs):
        defaults = {
            'ts_code': ['000001.SZ', '000001.SZ'],
            'trade_date': ['20180718', '20180717'],
            'close': [8.70, 8.72],
            'open': [8.75, 8.74],
        }
        defaults.update(kwargs)
        return pd.DataFrame(defaults)

    def test_extracts_column_values(self):
        logic = ColumnExtractLogic()
        df = self._make_df()
        result = logic.compute(df, {'column': 'close'})
        assert list(result.columns) == ['timestamp', 'symbol', 'value']
        assert len(result) == 2
        assert list(result['value']) == [8.70, 8.72]
        assert list(result['symbol']) == ['000001.SZ', '000001.SZ']

    def test_missing_column_returns_empty(self):
        logic = ColumnExtractLogic()
        df = self._make_df()
        result = logic.compute(df, {'column': 'nonexistent'})
        assert result.empty

    def test_yyyymmdd_date_parsing(self):
        logic = ColumnExtractLogic()
        df = self._make_df()
        result = logic.compute(df, {'column': 'close'})
        assert result['timestamp'].iloc[0] == datetime(2018, 7, 18)
        assert result['timestamp'].iloc[1] == datetime(2018, 7, 17)

    def test_uses_symbol_column_when_present(self):
        logic = ColumnExtractLogic()
        df = pd.DataFrame({
            'symbol': ['TEST.SZ'],
            'timestamp': [datetime(2024, 1, 1)],
            'close': [10.0],
        })
        result = logic.compute(df, {'column': 'close'})
        assert result['symbol'].iloc[0] == 'TEST.SZ'

    def test_missing_column_key_returns_empty(self):
        logic = ColumnExtractLogic()
        df = self._make_df()
        result = logic.compute(df, {})
        assert result.empty


class TestQuickRegisterConfig:
    def test_default_category(self):
        config = QuickRegisterConfig(data_source='my_source')
        assert config.category == 'QuickRegister'

    def test_default_prefix_empty(self):
        config = QuickRegisterConfig(data_source='my_source')
        assert config.prefix == ''

    def test_default_fields_none(self):
        config = QuickRegisterConfig(data_source='my_source')
        assert config.fields is None

    def test_custom_values(self):
        config = QuickRegisterConfig(
            data_source='src', fields=['close'], prefix='daily_', category='Price'
        )
        assert config.fields == ['close']
        assert config.prefix == 'daily_'
        assert config.category == 'Price'


class TestDetectFactorColumns:
    def test_excludes_identifier_columns(self):
        df = pd.DataFrame({
            'ts_code': ['a'], 'trade_date': ['20240101'],
            'close': [1.0], 'vol': [100.0]
        })
        cols = detect_factor_columns(df)
        assert 'ts_code' not in cols
        assert 'trade_date' not in cols
        assert 'close' in cols
        assert 'vol' in cols

    def test_excludes_non_numeric(self):
        df = pd.DataFrame({'ts_code': ['a'], 'name': ['foo'], 'close': [1.0]})
        cols = detect_factor_columns(df)
        assert 'name' not in cols
        assert 'close' in cols
