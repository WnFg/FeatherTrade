from src.trading_system.factors.base import BaseFactorLogic, BaseDataSource
import pandas as pd
from typing import Dict, Any
from datetime import datetime

class ExtensionLogic(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        multiplier = config.get('multiplier', 1.0)
        res = data[['timestamp', 'symbol']].copy()
        res['value'] = data['price'] * multiplier
        return res

class ExtensionSource(BaseDataSource):
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        data = {
            'timestamp': [start_time, end_time],
            'symbol': [symbol, symbol],
            'price': [10.0, 20.0]
        }
        return pd.DataFrame(data)
