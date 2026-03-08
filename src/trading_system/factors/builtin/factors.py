import pandas as pd
from typing import Dict, Any
from src.trading_system.factors.base import BaseFactorLogic

class MovingAverageFactor(BaseFactorLogic):
    """Calculates a Simple Moving Average (SMA) using pandas."""
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        window = config.get('window', 20)
        price_key = config.get('price_key', 'price')
        
        if data.empty or price_key not in data.columns:
            return pd.DataFrame()
            
        # Calculate SMA using pandas rolling
        res = data[['timestamp', 'symbol']].copy()
        res['value'] = data[price_key].rolling(window=window).mean()
        
        # Return only valid rows
        return res.dropna(subset=['value'])
