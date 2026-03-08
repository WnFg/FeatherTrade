import os
import importlib.util
import inspect
import logging
import yaml
from typing import List, Dict, Any, Optional, Type
from .models import FactorDefinition
from .base import BaseDataSource, BaseFactorLogic
from .config import FactorConfig, DataSourceConfig, ScheduleConfig

logger = logging.getLogger(__name__)

class DiscoveryEngine:
    """Utility to scan directories and discover factor components."""

    @staticmethod
    def discover_components(directory: str, base_class: Type) -> Dict[str, Type]:
        """
        Scans a directory for Python files and identifies classes that inherit from base_class.
        Returns a dictionary mapping class name (lowercase) to the class itself.
        """
        components = {}
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return components

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    module_name = file[:-3]

                    try:
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                if issubclass(obj, base_class) and obj is not base_class:
                                    # Use lowercase class name as key for consistency
                                    components[name.lower()] = obj
                    except Exception as e:
                        logger.error(f"Failed to load module {file_path}: {e}")

        return components

    @staticmethod
    def discover_configs(directory: str) -> Dict[str, List[Any]]:
        """
        Scans a directory for config variables and YAML files.
        Returns dict with keys: 'factor_configs', 'data_source_configs', 'schedule_configs'
        """
        configs = {
            'factor_configs': [],
            'data_source_configs': [],
            'schedule_configs': []
        }

        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return configs

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)

                # Scan Python files for module-level config variables
                if file.endswith(".py") and file != "__init__.py":
                    try:
                        spec = importlib.util.spec_from_file_location(file[:-3], file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            # Look for FACTOR_CONFIGS, DATA_SOURCE_CONFIGS, SCHEDULE_CONFIGS
                            if hasattr(module, 'FACTOR_CONFIGS'):
                                configs['factor_configs'].extend(module.FACTOR_CONFIGS)
                            if hasattr(module, 'DATA_SOURCE_CONFIGS'):
                                configs['data_source_configs'].extend(module.DATA_SOURCE_CONFIGS)
                            if hasattr(module, 'SCHEDULE_CONFIGS'):
                                configs['schedule_configs'].extend(module.SCHEDULE_CONFIGS)
                    except Exception as e:
                        logger.error(f"Failed to load config from {file_path}: {e}")

                # Scan YAML files
                elif file.endswith(".yaml") or file.endswith(".yml"):
                    try:
                        with open(file_path, 'r') as f:
                            data = yaml.safe_load(f)
                            if not data:
                                continue

                            # Parse YAML structure
                            if 'factor_configs' in data:
                                configs['factor_configs'].extend([
                                    FactorConfig.from_dict(c) for c in data['factor_configs']
                                ])
                            if 'data_source_configs' in data:
                                configs['data_source_configs'].extend([
                                    DataSourceConfig.from_dict(c) for c in data['data_source_configs']
                                ])
                            if 'schedule_configs' in data:
                                configs['schedule_configs'].extend([
                                    ScheduleConfig.from_dict(c) for c in data['schedule_configs']
                                ])
                    except Exception as e:
                        logger.error(f"Failed to load YAML config from {file_path}: {e}")

        return configs

class FactorRegistry:
    """Management of factor definitions and dynamic component discovery."""

    def __init__(self, db, builtin_dir: str, extensions_dir: str):
        self.db = db
        self.builtin_dir = builtin_dir
        self.extensions_dir = extensions_dir

        # Maps for dynamic components: { 'namespace.name': Class }
        self._logic_classes: Dict[str, Type[BaseFactorLogic]] = {}
        self._source_classes: Dict[str, Type[BaseDataSource]] = {}

        # Maps for config-driven instances
        self._ds_config_map: Dict[str, DataSourceConfig] = {}
        self._schedule_config_map: Dict[str, ScheduleConfig] = {}

        self.discover_all()

    def discover_all(self):
        """Discovers all components and configs from builtin and extensions directories."""
        # Discover Builtins
        builtin_logics = DiscoveryEngine.discover_components(
            os.path.join(self.builtin_dir, "factors") if os.path.isdir(os.path.join(self.builtin_dir, "factors")) else self.builtin_dir,
            BaseFactorLogic
        )
        builtin_sources = DiscoveryEngine.discover_components(
            os.path.join(self.builtin_dir, "data_sources") if os.path.isdir(os.path.join(self.builtin_dir, "data_sources")) else self.builtin_dir,
            BaseDataSource
        )

        for name, cls in builtin_logics.items():
            self._logic_classes[f"builtin.{name}"] = cls
            # Also register without prefix as fallback if not conflicting
            self._logic_classes[name] = cls

        for name, cls in builtin_sources.items():
            self._source_classes[f"builtin.{name}"] = cls
            self._source_classes[name] = cls

        # Discover Extensions (and override without prefix if exists)
        ext_logics = DiscoveryEngine.discover_components(self.extensions_dir, BaseFactorLogic)
        ext_sources = DiscoveryEngine.discover_components(self.extensions_dir, BaseDataSource)

        for name, cls in ext_logics.items():
            self._logic_classes[f"extensions.{name}"] = cls
            # User extensions override builtins for the unprefixed name
            self._logic_classes[name] = cls

        for name, cls in ext_sources.items():
            self._source_classes[f"extensions.{name}"] = cls
            self._source_classes[name] = cls

        # Discover configs from extensions
        configs = DiscoveryEngine.discover_configs(self.extensions_dir)

        # Register configs
        self._register_factor_configs(configs['factor_configs'])
        self._register_data_source_configs(configs['data_source_configs'])
        self._register_schedule_configs(configs['schedule_configs'])

    def get_logic_class(self, name: str) -> Optional[Type[BaseFactorLogic]]:
        return self._logic_classes.get(name.lower())

    def get_source_class(self, name: str) -> Optional[Type[BaseDataSource]]:
        return self._source_classes.get(name.lower())

    def register_factor(self, definition: FactorDefinition) -> int:
        """Registers a new factor definition in the database."""
        return self.db.insert_factor_definition(definition)

    def get_factor(self, name: str) -> Optional[FactorDefinition]:
        """Retrieves a factor definition from the database."""
        return self.db.get_factor_definition(name)

    def get_factor_by_id(self, factor_id: int) -> Optional[FactorDefinition]:
        """Retrieves a factor definition by its database ID."""
        sql = "SELECT * FROM factor_definitions WHERE id = ?"
        with self.db._get_connection() as conn:
            cursor = conn.execute(sql, (factor_id,))
            row = cursor.fetchone()
            if row:
                return FactorDefinition.from_db_row(row)
        return None

    def list_factors(self, category: Optional[str] = None) -> List[FactorDefinition]:
        """Lists all registered factors from the database."""
        return self.db.get_all_factor_definitions(category)

    def _register_factor_configs(self, configs: List[FactorConfig]) -> None:
        """Upsert FactorConfig entries to factor_definitions table (idempotent)."""
        for config in configs:
            try:
                # Check if factor already exists
                existing = self.db.get_factor_definition(config.name)
                if existing:
                    # Update if changed (simple approach: always update)
                    logger.info(f"Updating existing factor definition: {config.name}")
                    # For now, skip update logic - just log
                else:
                    # Insert new
                    factor_def = FactorDefinition(
                        id=None,
                        name=config.name,
                        display_name=config.display_name or config.name,
                        category=config.category,
                        description=config.description,
                        formula_config=config.formula_config,
                        version=config.version
                    )
                    self.db.insert_factor_definition(factor_def)
                    logger.info(f"Registered factor from config: {config.name}")
            except Exception as e:
                logger.error(f"Failed to register factor config {config.name}: {e}")

    def _register_data_source_configs(self, configs: List[DataSourceConfig]) -> None:
        """Store DataSourceConfig in memory map."""
        for config in configs:
            self._ds_config_map[config.name] = config
            logger.info(f"Registered data source config: {config.name}")

    def _register_schedule_configs(self, configs: List[ScheduleConfig]) -> None:
        """Store ScheduleConfig in memory map."""
        for config in configs:
            self._schedule_config_map[config.name] = config
            logger.info(f"Registered schedule config: {config.name}")

    def get_data_source_config(self, name: str) -> Optional[DataSourceConfig]:
        """Retrieve a DataSourceConfig by name."""
        return self._ds_config_map.get(name)

    def get_schedule_config(self, name: str) -> Optional[ScheduleConfig]:
        """Retrieve a ScheduleConfig by name."""
        return self._schedule_config_map.get(name)
