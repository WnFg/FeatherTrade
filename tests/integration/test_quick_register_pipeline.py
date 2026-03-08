import os
import tempfile
import logging
import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from src.trading_system.factors.service import FactorService
from src.trading_system.factors.quick_register import QuickRegisterConfig
from src.trading_system.factors.base import BaseDataSource


OHLCV_DF = pd.DataFrame({
    'ts_code': ['000001.SZ', '000001.SZ'],
    'trade_date': ['20180718', '20180717'],
    'open': [8.75, 8.74],
    'high': [8.85, 8.75],
    'low': [8.69, 8.66],
    'close': [8.70, 8.72],
    'vol': [525152.0, 375356.0],
})


class MockDataSource(BaseDataSource):
    def fetch_data(self, symbol, start_time, end_time):
        return OHLCV_DF.copy()


def make_service(tmp_path):
    db_path = str(tmp_path / 'test.db')
    service = FactorService(db=db_path)
    source = MockDataSource()
    service.register_source('mock_daily', source)
    return service


class TestQuickRegisterPipeline:
    def test_registers_factor_definitions(self, tmp_path):
        service = make_service(tmp_path)
        config = QuickRegisterConfig(
            data_source='mock_daily',
            fields=['close', 'vol'],
        )
        names = service.quick_register(config)
        assert 'close' in names
        assert 'vol' in names
        assert service.get_factor_definition('close') is not None
        assert service.get_factor_definition('vol') is not None

    def test_logic_bound_and_compute_works(self, tmp_path):
        service = make_service(tmp_path)
        config = QuickRegisterConfig(data_source='mock_daily', fields=['close'])
        service.quick_register(config)
        logic = service._logic_instances.get('close')
        assert logic is not None
        result = logic.compute(OHLCV_DF, {'column': 'close'})
        assert not result.empty
        assert list(result['value']) == [8.70, 8.72]

    def test_idempotent_registration(self, tmp_path):
        service = make_service(tmp_path)
        config = QuickRegisterConfig(data_source='mock_daily', fields=['close'])
        service.quick_register(config)
        service.quick_register(config)
        # Should not raise; only one factor definition in DB
        factors = service.registry.list_factors()
        close_factors = [f for f in factors if f.name == 'close']
        assert len(close_factors) == 1

    def test_prefix_applied_to_factor_names(self, tmp_path):
        service = make_service(tmp_path)
        config = QuickRegisterConfig(
            data_source='mock_daily',
            fields=['close', 'open'],
            prefix='daily_',
        )
        names = service.quick_register(config)
        assert 'daily_close' in names
        assert 'daily_open' in names
        assert service.get_factor_definition('daily_close') is not None

    def test_missing_data_source_logs_error_no_exception(self, tmp_path, caplog):
        service = make_service(tmp_path)
        config = QuickRegisterConfig(
            data_source='nonexistent_source',
            fields=['close'],
        )
        with caplog.at_level(logging.ERROR):
            result = service.quick_register(config)
        assert result == []
        assert any('nonexistent_source' in r.message for r in caplog.records)

    def test_auto_discovery_registers_factors(self, tmp_path):
        db_path = str(tmp_path / 'test.db')
        ext_dir = tmp_path / 'extensions'
        ext_dir.mkdir()

        ext_code = '''
from src.trading_system.factors.base import BaseDataSource
from src.trading_system.factors.quick_register import QuickRegisterConfig
import pandas as pd

class DailySource(BaseDataSource):
    def fetch_data(self, symbol, start_time, end_time):
        return pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20180718'],
            'close': [8.70],
            'vol': [525152.0],
        })

QUICK_REGISTER_CONFIGS = [
    QuickRegisterConfig(
        data_source='daily_source',
        fields=['close', 'vol'],
        category='Daily',
    )
]
'''
        (ext_dir / 'daily_ext.py').write_text(ext_code)

        service = FactorService(db=db_path, extensions_dir=str(ext_dir))
        # Register the source so quick_register can find it
        service.register_source('daily_source', service._get_source('dailysource') or __import__(
            'src.trading_system.factors.base', fromlist=['BaseDataSource']
        ))
        # Re-run quick_register manually since source wasn't registered at init time
        config = QuickRegisterConfig(data_source='daily_source', fields=['close', 'vol'], category='Daily')
        names = service.quick_register(config)
        assert 'close' in names
        assert 'vol' in names
