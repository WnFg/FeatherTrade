import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ParameterTransformer:
    """Utility to transform DataFrames based on a configuration."""

    @staticmethod
    def transform(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Applies transformations to a DataFrame based on config.
        Supported transformations:
        - rename: { 'old_name': 'new_name' } (alias for column_mapping)
        - column_mapping: { 'old_name': 'new_name' }
        - type_casting: { 'column_name': 'target_type' } (e.g. 'int', 'float', 'datetime')
        """
        if df.empty:
            return df

        # 1. Column Mapping (support both 'rename' and 'column_mapping' keys)
        column_mapping = config.get('rename') or config.get('column_mapping', {})
        if column_mapping:
            # Only rename columns that exist
            actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=actual_mapping)

        # 2. Type Casting
        type_casting = config.get('type_casting', {})
        for col, target_type in type_casting.items():
            if col in df.columns:
                try:
                    if target_type == 'int':
                        df[col] = df[col].astype(int)
                    elif target_type == 'float':
                        df[col] = df[col].astype(float)
                    elif target_type == 'datetime':
                        df[col] = pd.to_datetime(df[col])
                    # Add more types as needed
                except Exception as e:
                    logger.warning(f"Failed to cast column '{col}' to {target_type}: {e}")

        return df
