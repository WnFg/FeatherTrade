# Factor Extension Examples

Step-by-step examples for registering custom factors, data sources, and scheduled ingestion tasks.

---

## 1. Registering a Custom Factor

Create a `.py` file in `src/trading_system/factors/extensions/` with a class inheriting `BaseFactorLogic`:

```python
# extensions/my_factors.py
import pandas as pd
from typing import Dict, Any
from src.trading_system.factors.base import BaseFactorLogic

class MyMovingAverage(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        window = config.get("window", 20)
        return pd.DataFrame({
            "timestamp": data["timestamp"],
            "symbol":    data["symbol"],
            "value":     data["close"].rolling(window).mean(),
        })
```

`FactorService` auto-discovers all `BaseFactorLogic` subclasses in `extensions/` at startup — no registration code needed.

---

## 2. Registering a Custom Data Source

Inherit from `BaseDataSource` and implement `fetch_data`:

```python
# extensions/my_data_source.py
import pandas as pd
from datetime import datetime
from src.trading_system.factors.base import BaseDataSource

class MyCSVSource(BaseDataSource):
    def configure(self, params: dict):
        self._file = params.get("file", "data.csv")

    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        df = pd.read_csv(self._file)
        df = df[df["symbol"] == symbol]
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]
```

The returned DataFrame must have at least:
- A timestamp column: `timestamp` or `trade_date`
- A symbol column: `symbol` or `ts_code`
- One or more numeric value columns

---

## 3. Declarative Config Registration

Define `FACTOR_CONFIGS`, `DATA_SOURCE_CONFIGS`, and optionally `SCHEDULE_CONFIGS` as module-level variables:

```python
# extensions/value_factors.py
from src.trading_system.factors.base import BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig
import pandas as pd
from typing import Dict, Any

class PEFactor(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        return pd.DataFrame({
            "timestamp": data["timestamp"],
            "symbol":    data["symbol"],
            "value":     data["pe"].astype(float),
        })

FACTOR_CONFIGS = [
    FactorConfig(name="pefactor", category="Value", display_name="P/E Ratio"),
]

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_basic_600519",
        source_class="TuShareDataSource",
        params={"api": "daily_basic", "symbols": ["600519.SH"]},
        time_range={"start": "today-365d", "end": "today"},
    )
]

SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_job",
        factor="pefactor",
        data_source="tushare_basic_600519",
        trigger={"type": "cron", "expr": "0 18 * * 1-5"},  # weekdays at 18:00
    )
]
```

---

## 4. Scheduled Ingestion

To run a scheduled ingestion pipeline:

```python
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.scheduler import TaskScheduler
from src.trading_system.factors.settings import DB_PATH
import time

service   = FactorService(db=DB_PATH)   # auto-discovers extensions/
scheduler = TaskScheduler(service)
scheduler.load_all_config_tasks()       # registers all SCHEDULE_CONFIGS
scheduler.start()

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    scheduler.stop()
```

### Trigger Types

| Type | Example | Description |
|---|---|---|
| `cron` | `{"type": "cron", "expr": "0 18 * * 1-5"}` | Weekdays at 18:00 |
| `interval` | `{"type": "interval", "seconds": 3600}` | Every hour |
| `one-off` | `{"type": "one-off", "run_time": "2025-06-01T09:00:00"}` | Run once |

---

## 5. Relative Time Ranges

`DataSourceConfig.time_range` supports relative expressions, resolved at job execution time:

| Expression | Meaning |
|---|---|
| `today` | Today at 00:00:00 |
| `today-Nd` | N days ago (e.g. `today-3d`) |
| `today-Nw` | N weeks ago (e.g. `today-1w`) |
| `2025-01-01` | Fixed ISO 8601 date |

---

## 6. Manual Ingestion

Trigger a factor computation run directly without the scheduler:

```python
from datetime import datetime
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.settings import DB_PATH

svc = FactorService(db=DB_PATH)
svc.compute_and_store(
    symbol="000001.SZ",
    factor_name="daily_close",
    source_name="tushare_daily",
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2026, 1, 1),
)
```

---

## 7. Verifying Registration

```python
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.settings import DB_PATH

svc = FactorService(db=DB_PATH)

# Check factor definition
defn = svc.get_factor_definition("daily_close")
print(defn)

# Check data source config
ds = svc.registry.get_data_source_config("tushare_daily")
print(ds)

# Query stored values
values = svc.get_factor_values("000001.SZ", "daily_close", limit=5)
for v in values:
    print(v.timestamp, v.value)
```
