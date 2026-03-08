"""
Integration tests for config-driven factor pipeline.

Tests the full workflow: extension file → register factor → instantiate data source
→ execute scheduled task → verify factor_values write.
"""
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import pandas as pd

from src.trading_system.factors.service import FactorService
from src.trading_system.factors.registry import FactorRegistry
from src.trading_system.factors.scheduler import TaskScheduler
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig


@pytest.fixture
def temp_extensions_dir():
    """Create a temporary extensions directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = FactorDatabase(path)
    yield db
    db.close()
    os.unlink(path)


@pytest.fixture
def factor_service(temp_db, temp_extensions_dir):
    """Create a FactorService with temporary database and extensions directory."""
    service = FactorService(db_path=temp_db.db_path)
    service.registry.extensions_dir = temp_extensions_dir
    return service


class TestConfigDrivenPipeline:
    """Test the full config-driven factor pipeline."""

    def test_python_extension_to_factor_values(self, factor_service, temp_extensions_dir):
        """Test: extension file → register → instantiate → execute → verify write."""
        # Create a mock data source extension
        extension_code = '''
from datetime import datetime
import pandas as pd
from src.trading_system.factors.base import BaseDataSource, BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig

class MockDataSource(BaseDataSource):
    def configure(self, params):
        self.multiplier = params.get('multiplier', 1.0)

    def fetch_data(self, symbol, start_time, end_time):
        # Return mock data
        dates = pd.date_range(start_time, end_time, freq='D')
        return pd.DataFrame({
            'date': dates,
            'value': [100.0 * self.multiplier] * len(dates)
        })

class SimpleFactor(BaseFactorLogic):
    def compute(self, data):
        return data['value'].mean()

FACTOR_CONFIGS = [
    FactorConfig(
        name='simple_factor',
        category='test',
        display_name='Simple Test Factor'
    )
]

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name='mock_source',
        source_class='MockDataSource',
        params={'multiplier': 2.0}
    )
]
'''
        extension_file = Path(temp_extensions_dir) / 'test_extension.py'
        extension_file.write_text(extension_code)

        # Discover and register
        factor_service.registry.discover_all()

        # Verify factor registered
        factor_def = factor_service.db.get_factor_definition('simple_factor')
        assert factor_def is not None
        assert factor_def['category'] == 'test'

        # Verify data source config registered
        ds_config = factor_service.registry.get_data_source_config('mock_source')
        assert ds_config is not None
        assert ds_config.params['multiplier'] == 2.0

        # Execute compute_and_store
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 5)
        factor_service.compute_and_store(
            symbol='TEST001',
            factor_name='simple_factor',
            data_source_name='mock_source',
            start_time=start,
            end_time=end
        )

        # Verify factor_values written
        values = factor_service.db.get_factor_values(
            symbol='TEST001',
            factor_name='simple_factor',
            start_time=start,
            end_time=end
        )
        assert len(values) > 0
        assert values[0]['value'] == 200.0  # 100 * 2.0 multiplier

    def test_yaml_extension_to_factor_values(self, factor_service, temp_extensions_dir):
        """Test: YAML config → register → instantiate → execute → verify write."""
        # Create Python module with classes
        module_code = '''
from datetime import datetime
import pandas as pd
from src.trading_system.factors.base import BaseDataSource, BaseFactorLogic

class YamlMockSource(BaseDataSource):
    def configure(self, params):
        self.offset = params.get('offset', 0)

    def fetch_data(self, symbol, start_time, end_time):
        dates = pd.date_range(start_time, end_time, freq='D')
        return pd.DataFrame({
            'date': dates,
            'metric': [50.0 + self.offset] * len(dates)
        })

class YamlFactor(BaseFactorLogic):
    def compute(self, data):
        return data['metric'].sum()
'''
        module_file = Path(temp_extensions_dir) / 'yaml_module.py'
        module_file.write_text(module_code)

        # Create YAML config
        yaml_config = '''
factors:
  - name: yaml_factor
    category: yaml_test
    display_name: YAML Test Factor

data_sources:
  - name: yaml_mock_source
    source_class: YamlMockSource
    params:
      offset: 10
'''
        yaml_file = Path(temp_extensions_dir) / 'yaml_config.yaml'
        yaml_file.write_text(yaml_config)

        # Discover and register
        factor_service.registry.discover_all()

        # Verify registration
        factor_def = factor_service.db.get_factor_definition('yaml_factor')
        assert factor_def is not None
        assert factor_def['category'] == 'yaml_test'

        ds_config = factor_service.registry.get_data_source_config('yaml_mock_source')
        assert ds_config is not None
        assert ds_config.params['offset'] == 10

        # Execute
        start = datetime(2024, 2, 1)
        end = datetime(2024, 2, 3)
        factor_service.compute_and_store(
            symbol='YAML001',
            factor_name='yaml_factor',
            data_source_name='yaml_mock_source',
            start_time=start,
            end_time=end
        )

        # Verify
        values = factor_service.db.get_factor_values(
            symbol='YAML001',
            factor_name='yaml_factor',
            start_time=start,
            end_time=end
        )
        assert len(values) > 0
        assert values[0]['value'] == 180.0  # (50 + 10) * 3 days

    def test_relative_time_range_resolution(self, factor_service, temp_extensions_dir):
        """Test: relative time range resolution at different execution dates."""
        from src.trading_system.factors.time_resolver import TimeRangeResolver
        from unittest.mock import patch

        # Create extension with relative time range
        extension_code = '''
from datetime import datetime
import pandas as pd
from src.trading_system.factors.base import BaseDataSource, BaseFactorLogic
from src.trading_system.factors.config import DataSourceConfig

class TimeTestSource(BaseDataSource):
    def fetch_data(self, symbol, start_time, end_time):
        # Return the time range as data
        return pd.DataFrame({
            'start': [start_time],
            'end': [end_time],
            'days': [(end_time - start_time).days]
        })

class TimeTestFactor(BaseFactorLogic):
    def compute(self, data):
        return data['days'].iloc[0]

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name='time_test_source',
        source_class='TimeTestSource',
        time_range={'start': 'today-7d', 'end': 'today'}
    )
]
'''
        extension_file = Path(temp_extensions_dir) / 'time_test.py'
        extension_file.write_text(extension_code)

        factor_service.registry.discover_all()

        # Mock datetime.now() to test different execution dates
        base_date = datetime(2024, 3, 15, 12, 0, 0)
        with patch('src.trading_system.factors.time_resolver.datetime') as mock_dt:
            mock_dt.now.return_value = base_date
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.strptime = datetime.strptime

            # Get data source config
            ds_config = factor_service.registry.get_data_source_config('time_test_source')

            # Resolve time range
            resolver = TimeRangeResolver()
            start = resolver.resolve(ds_config.time_range['start'])
            end = resolver.resolve(ds_config.time_range['end'])

            # Verify resolution
            assert start == datetime(2024, 3, 8, 0, 0, 0)  # 7 days before
            assert end == datetime(2024, 3, 15, 0, 0, 0)  # today at midnight

    def test_multi_symbol_expansion(self, factor_service, temp_extensions_dir):
        """Test: multi-symbol list expansion, each symbol gets independent compute_and_store."""
        extension_code = '''
from datetime import datetime
import pandas as pd
from src.trading_system.factors.base import BaseDataSource, BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig

class MultiSymbolSource(BaseDataSource):
    def fetch_data(self, symbol, start_time, end_time):
        # Return symbol-specific data
        return pd.DataFrame({
            'symbol': [symbol],
            'metric': [len(symbol)]  # Use symbol length as metric
        })

class SymbolFactor(BaseFactorLogic):
    def compute(self, data):
        return data['metric'].iloc[0]

FACTOR_CONFIGS = [
    FactorConfig(name='symbol_factor', category='test')
]

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name='multi_symbol_source',
        source_class='MultiSymbolSource',
        params={'symbols': ['SYM1', 'SYMBOL2', 'SYM']}
    )
]
'''
        extension_file = Path(temp_extensions_dir) / 'multi_symbol.py'
        extension_file.write_text(extension_code)

        factor_service.registry.discover_all()

        # Execute for all symbols
        ds_config = factor_service.registry.get_data_source_config('multi_symbol_source')
        symbols = ds_config.params['symbols']

        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 2)

        for symbol in symbols:
            factor_service.compute_and_store(
                symbol=symbol,
                factor_name='symbol_factor',
                data_source_name='multi_symbol_source',
                start_time=start,
                end_time=end
            )

        # Verify each symbol has its own value
        for symbol in symbols:
            values = factor_service.db.get_factor_values(
                symbol=symbol,
                factor_name='symbol_factor',
                start_time=start,
                end_time=end
            )
            assert len(values) > 0
            assert values[0]['value'] == len(symbol)

