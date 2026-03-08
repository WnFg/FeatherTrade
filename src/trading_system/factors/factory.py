import importlib
import logging
from typing import Dict, Any, Type, Optional
from .base import BaseDataSource

logger = logging.getLogger(__name__)

class DataSourceFactory:
    """Factory for creating data source instances from database configurations."""

    # Static registry of built-in templates
    TEMPLATES = {
        'TuShareDataSource': 'src.trading_system.factors.builtin.data_sources.TuShareDataSource',
        'FileDataSource': 'src.trading_system.factors.builtin.data_sources.FileDataSource',
        'APIDataSource': 'src.trading_system.factors.builtin.data_sources.APIDataSource'
    }

    @staticmethod
    def create_instance(class_path: str, parameters: Dict[str, Any]) -> BaseDataSource:
        """
        Instantiates a BaseDataSource subclass from a class path and parameters.
        class_path can be a full path or a short name from TEMPLATES.
        """
        actual_path = DataSourceFactory.TEMPLATES.get(class_path, class_path)

        try:
            # Handle both full paths (module.Class) and simple class names (Class)
            if '.' in actual_path:
                module_path, class_name = actual_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)
            else:
                # Simple class name - assume it's already imported in the current context
                # This shouldn't happen in normal usage, but handle gracefully
                raise ValueError(f"Class path must include module: {class_path}")

            if not issubclass(cls, BaseDataSource):
                raise ValueError(f"Class {actual_path} is not a subclass of BaseDataSource")

            # Try instantiation with no-arg constructor first
            try:
                instance = cls()
            except TypeError:
                # Fallback: try with parameters if no-arg constructor fails
                instance = cls(**parameters)

            # Call configure() with parameters after instantiation
            instance.configure(parameters)

            return instance
        except Exception as e:
            logger.error(f"Failed to create data source instance {actual_path}: {e}")
            raise

    @staticmethod
    def get_templates() -> Dict[str, str]:
        """Returns the dictionary of available data source templates."""
        return DataSourceFactory.TEMPLATES
