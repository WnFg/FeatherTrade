# Factor Extensions

This directory is the standard extension point for adding custom factor logic and data sources to the trading system.

## How to add a Custom Factor

1.  Create a new Python file in this directory (e.g., `my_custom_factor.py`).
2.  Define a class that inherits from `src.trading_system.factors.base.BaseFactorLogic`.
3.  Implement the `compute` method.

```python
from src.trading_system.factors.base import BaseFactorLogic
import pandas as pd
from typing import Dict, Any

class MyCustomFactor(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        # Your calculation logic here
        # Input 'data' is a pandas DataFrame from the data source
        # Returns a DataFrame with 'timestamp', 'value' (and optionally 'symbol')
        res = data[['timestamp', 'symbol']].copy()
        res['value'] = data['close'] - data['open'] # Example: intra-day range
        return res
```

4.  Register the factor in the system using the lowercase class name (e.g., `mycustomfactor`) as the factor name in your configuration or database.

## How to add a Custom Data Source

1.  Create a new Python file in this directory (e.g., `my_custom_source.py`).
2.  Define a class that inherits from `src.trading_system.factors.base.BaseDataSource`.
3.  Implement the `fetch_data` method.

```python
from src.trading_system.factors.base import BaseDataSource
import pandas as pd
from datetime import datetime

class MyCustomSource(BaseDataSource):
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        # Your data fetching logic here (e.g., from a proprietary API)
        # Returns a pandas DataFrame with 'timestamp', 'symbol', and required data columns
        return pd.DataFrame(...)
```

4.  Reference the data source in the system using its lowercase class name (e.g., `mycustomsource`).

## Dynamic Discovery

The system automatically scans this directory and registers any valid subclasses of `BaseFactorLogic` and `BaseDataSource`.

### Namespacing
Extensions are available via their simple name (e.g., `mycustomfactor`) and their namespaced name (e.g., `extensions.mycustomfactor`). If a name conflict occurs with a built-in component, the extension takes precedence for the simple name.
