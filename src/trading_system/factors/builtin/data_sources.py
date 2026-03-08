import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from src.trading_system.factors.base import BaseDataSource

class FileDataSource(BaseDataSource):
    """Simple data source that reads raw data from a CSV file."""
    def __init__(self, file_path: str = None):
        self.file_path = file_path

    def configure(self, params: Dict[str, Any]) -> None:
        """Configure with file_path parameter."""
        if 'file_path' in params:
            self.file_path = params['file_path']

    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        if not self.file_path:
            raise ValueError("FileDataSource not configured with file_path")

        df = pd.read_csv(self.file_path)

        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Filter by symbol and time range
        mask = (df['symbol'] == symbol) & (df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)
        result_df = df.loc[mask].copy()

        # Normalize types and ensure consistent column order
        if 'price' in result_df.columns:
            result_df['price'] = result_df['price'].astype(float)

        return result_df.sort_values('timestamp')

class APIDataSource(BaseDataSource):
    """Skeleton for an API-based data source."""
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    def configure(self, params: Dict[str, Any]) -> None:
        """Configure with api_key and base_url parameters."""
        if 'api_key' in params:
            self.api_key = params['api_key']
        if 'base_url' in params:
            self.base_url = params['base_url']

    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        # In a real implementation, use requests or similar to fetch from the API
        print(f"Fetch data from {self.base_url} for {symbol}")
        return pd.DataFrame()

class TuShareDataSource(BaseDataSource):
    """Data source that fetches data from TuShare SDK."""
    def __init__(self):
        """No-arg constructor for discovery. Use configure() to set parameters."""
        self.token = None
        self.pro = None
        self.api = 'daily'  # Default API endpoint
        self.fields = None
        self.symbols = []
        self.custom_params = {}

    def configure(self, params: Dict[str, Any]) -> None:
        """
        Configure TuShare data source with runtime parameters.

        Args:
            params: Configuration dict with keys:
                - api: API endpoint name ('daily', 'daily_basic', etc.)
                - fields: List of fields to fetch (optional)
                - symbols: List of symbols (optional, for reference)
                - token: TuShare token (optional, defaults to env var)
                - **other: Additional query parameters
        """
        import tushare as ts
        import os
        import tushare.pro.client as client

        client.DataApi._DataApi__http_url = "http://tushare.xyz"

        self.token = params.get('token') or os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("TuShare token must be provided via params or TUSHARE_TOKEN environment variable")

        try:
            self.pro = ts.pro_api(self.token)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize TuShare API: {e}")

        self.api = params.get('api', 'daily')
        self.fields = params.get('fields')
        self.symbols = params.get('symbols', [])

        # Store other params for query
        self.custom_params = {k: v for k, v in params.items()
                             if k not in ['api', 'fields', 'symbols', 'token']}

    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """
        Fetches data from TuShare and maps columns to internal standard.
        Standard columns: symbol, timestamp, price, volume, etc.
        """
        if not self.pro:
            raise RuntimeError("TuShareDataSource not configured. Call configure() first.")

        # Convert datetime to YYYYMMDD string
        s_date = start_time.strftime('%Y%m%d')
        e_date = end_time.strftime('%Y%m%d')

        # Build query params
        query_params = {
            'ts_code': symbol,
            'start_date': s_date,
            'end_date': e_date,
            **self.custom_params
        }

        if self.fields:
            query_params['fields'] = ','.join(self.fields) if isinstance(self.fields, list) else self.fields

        try:
            # Dynamically call the pro API method
            api_method = getattr(self.pro, self.api)
            df = api_method(**query_params)

            if df.empty:
                return df

            # Standard column mapping
            rename_map = {
                'ts_code': 'symbol',
                'trade_date': 'timestamp',
                'vol': 'volume'
            }
            # Only rename if columns exist
            actual_rename = {k: v for k, v in rename_map.items() if k in df.columns}
            df = df.rename(columns=actual_rename)

            # Convert timestamp string to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y%m%d')

            return df.sort_values('timestamp') if 'timestamp' in df.columns else df

        except Exception as e:
            # In a real system, handle specific rate limit errors from TuShare
            print(f"Error fetching data from TuShare ({self.api}): {e}")
            return pd.DataFrame()
