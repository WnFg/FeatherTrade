import pandas as pd
import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from .models import FactorValue, FactorDefinition, DataSourceInstance
from .base import BaseDataSource, BaseFactorLogic
from .registry import FactorRegistry
from .factory import DataSourceFactory
from .transformer import ParameterTransformer
from .config import DataSourceConfig
from .database import FactorDatabase
from .quick_register import QuickRegisterConfig, ColumnExtractLogic, detect_factor_columns

logger = logging.getLogger(__name__)

class FactorService:
    """Main interface for interacting with the factor system."""
    def __init__(self, db: Union[FactorDatabase, str], builtin_dir: Optional[str] = None, extensions_dir: Optional[str] = None):
        # Support both FactorDatabase instance and db_path string
        if isinstance(db, str):
            self.db = FactorDatabase(db)
        else:
            self.db = db

        # Determine default directories if not provided
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if builtin_dir is None:
            builtin_dir = os.path.join(current_dir, "builtin")
        if extensions_dir is None:
            extensions_dir = os.path.join(current_dir, "extensions")

        self.registry = FactorRegistry(self.db, builtin_dir, extensions_dir)

        # logic_map and source_map now store INSTANCES, while registry stores CLASSES
        self._logic_instances: Dict[str, BaseFactorLogic] = {}
        self._source_instances: Dict[str, BaseDataSource] = {}
        self._cache: Dict[str, List[FactorValue]] = {}

        # Auto-execute discovered QuickRegisterConfigs
        for qr_config in self.registry.get_quick_register_configs():
            try:
                self.quick_register(qr_config)
            except Exception as e:
                logger.error(f"Auto quick_register failed for data_source={qr_config.data_source}: {e}")

    def register_logic(self, name: str, logic: BaseFactorLogic):
        """Explicitly register a logic instance (manual override)."""
        self._logic_instances[name.lower()] = logic

    def register_source(self, name: str, source: BaseDataSource):
        """Explicitly register a source instance (manual override)."""
        self._source_instances[name.lower()] = source

    def register_factor_definition(self, definition: FactorDefinition) -> int:
        """Persists a new factor metadata definition."""
        return self.registry.register_factor(definition)

    def get_factor_definition(self, name_or_id: Any) -> Optional[FactorDefinition]:
        """Retrieves a factor definition by name or ID."""
        if isinstance(name_or_id, int):
            return self.registry.get_factor_by_id(name_or_id)
        return self.registry.get_factor(name_or_id)

    def _get_logic(self, name: str) -> Optional[BaseFactorLogic]:
        """Gets a logic instance, instantiating it from the registry if needed."""
        name = name.lower()
        if name in self._logic_instances:
            return self._logic_instances[name]

        cls = self.registry.get_logic_class(name)
        if cls:
            instance = cls()
            self._logic_instances[name] = instance
            return instance
        return None

    def _get_source(self, name_or_id: Any) -> Optional[BaseDataSource]:
        """Gets a source instance, instantiating it from the registry or factory if needed."""
        # Check if it's already an instance name
        name = str(name_or_id).lower()
        if name in self._source_instances:
            return self._source_instances[name]

        # Priority 1: Check if it's a DataSourceConfig from registry
        ds_config = self.registry.get_data_source_config(name)
        if ds_config:
            instance = self._instantiate_from_config(ds_config)
            self._source_instances[name] = instance
            return instance

        # Priority 2: Check if it's a DataSourceInstance from DB
        ds_instance = self.db.get_data_source_instance(name_or_id)
        if ds_instance:
            instance = DataSourceFactory.create_instance(ds_instance.class_path, ds_instance.parameters)
            self._source_instances[name] = instance
            return instance

        # Priority 3: Fallback to dynamic registry (built-ins or extensions)
        cls = self.registry.get_source_class(name)
        if cls:
            try:
                instance = cls()
                self._source_instances[name] = instance
                return instance
            except TypeError:
                # Fallback or log if it requires parameters
                return None
        return None

    def _instantiate_from_config(self, config: DataSourceConfig) -> BaseDataSource:
        """Instantiate a BaseDataSource from a DataSourceConfig."""
        # Priority 1: Try to find the class in registry (discovered from extensions)
        cls = self.registry.get_source_class(config.source_class.lower())
        if cls:
            try:
                instance = cls()
            except TypeError:
                instance = cls(**config.params)
            instance.configure(config.params)
            return instance

        # Priority 2: Fall back to DataSourceFactory (handles TEMPLATES and full paths)
        return DataSourceFactory.create_instance(config.source_class, config.params)

    def get_factor_values(self, symbol: str, factor_name: str,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          limit: Optional[int] = None) -> List[FactorValue]:
        """Queries factor values from the database with a simple cache."""
        cache_key = f"{symbol}:{factor_name}:{start_time}:{end_time}:{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        values = self.db.query_factor_values(factor_name, symbol, start_time, end_time, limit)
        self._cache[cache_key] = values
        return values

    def clear_cache(self):
        """Clears the internal cache."""
        self._cache.clear()

    def get_factor_values_by_category(self, symbol: str, category: str,
                                      start_time: Optional[datetime] = None,
                                      end_time: Optional[datetime] = None) -> Dict[str, List[FactorValue]]:
        """Queries multiple factor values for a symbol within a category."""
        factors = self.registry.list_factors(category)
        result = {}
        for f in factors:
            result[f.name] = self.get_factor_values(symbol, f.name, start_time, end_time)
        return result

    def compute_and_store_batch(self, symbols: List[str], factor_names: List[str],
                                source_name: str, start_time: datetime, end_time: datetime):
        """Efficiently computes and stores multiple factors for multiple symbols."""
        for symbol in symbols:
            for factor_name in factor_names:
                self.compute_and_store(symbol, factor_name, source_name, start_time, end_time)

    def compute_and_store(self, symbol: str, factor_name: Any, source_name_or_id: Any,
                          start_time: datetime, end_time: datetime):
        """Coordinates data fetching, computation, and storage."""
        if isinstance(factor_name, int):
            factor_def = self.registry.get_factor_by_id(factor_name)
        else:
            factor_def = self.registry.get_factor(factor_name)

        if not factor_def:
            raise ValueError(f"Factor {factor_name} not registered")

        # Get data source (config-driven or DB-driven)
        source = self._get_source(source_name_or_id)
        if not source:
            raise ValueError(f"Source {source_name_or_id} not found or requires manual registration")

        logic = self._get_logic(factor_def.name)
        if not logic:
            raise ValueError(f"No computation logic found for factor {factor_name}")

        df = source.fetch_data(symbol, start_time, end_time)
        if df.empty:
            return

        # Apply transformations from DataSourceConfig or DB instance
        ds_config = self.registry.get_data_source_config(str(source_name_or_id).lower())
        if ds_config and ds_config.transformation:
            df = ParameterTransformer.transform(df, ds_config.transformation)
        else:
            # Fallback to DB instance transformation
            ds_instance = self.db.get_data_source_instance(source_name_or_id)
            if ds_instance and ds_instance.transformation_config:
                df = ParameterTransformer.transform(df, ds_instance.transformation_config)

        result_df = logic.compute(df, factor_def.formula_config)
        if result_df.empty:
            return

        computed_values = []
        for _, row in result_df.iterrows():
            computed_values.append(FactorValue(
                id=None,
                factor_id=factor_def.id,
                symbol=symbol if 'symbol' not in result_df.columns else row['symbol'],
                timestamp=row['timestamp'],
                value=float(row['value']),
                metadata=None
            ))

        self.db.insert_factor_values(computed_values)

    def quick_register(self, config: QuickRegisterConfig,
                        sample_symbol: Optional[str] = None,
                        sample_date: Optional[datetime] = None) -> List[str]:
        """Batch-register DataFrame columns as factors from a QuickRegisterConfig."""
        source = self._get_source(config.data_source)
        if source is None:
            logger.error(f"quick_register: data source '{config.data_source}' not found")
            return []

        if config.fields:
            fields = list(config.fields)
        else:
            if sample_symbol is None or sample_date is None:
                raise ValueError(
                    "quick_register requires sample_symbol and sample_date when fields is not specified"
                )
            sample_df = source.fetch_data(sample_symbol, sample_date, sample_date)
            if sample_df.empty:
                logger.warning(f"quick_register: sample fetch returned empty DataFrame for '{config.data_source}'")
                return []
            fields = detect_factor_columns(sample_df)
            if not fields:
                logger.warning(f"quick_register: no eligible numeric columns found in '{config.data_source}'")
                return []

        registered = []
        for field_name in fields:
            factor_name = f"{config.prefix}{field_name}" if config.prefix else field_name
            description = config.description_template.format(field=field_name)

            existing = self.registry.get_factor(factor_name)
            if not existing:
                factor_def = FactorDefinition(
                    id=None,
                    name=factor_name,
                    display_name=factor_name,
                    category=config.category,
                    description=description,
                    formula_config={"column": field_name, "quick_register": True},
                )
                self.registry.register_factor(factor_def)

            logic = ColumnExtractLogic()
            self._logic_instances[factor_name] = logic
            registered.append(factor_name)

        return registered
