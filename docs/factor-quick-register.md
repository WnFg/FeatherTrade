# Factor Quick Register

Quick Register lets you batch-register a full set of factors from a single `QuickRegisterConfig` — no need to define each factor individually.

## How It Works

1. Define a `DataSourceConfig` pointing to an API that returns a DataFrame
2. Define a `QuickRegisterConfig` listing which columns to extract as factors
3. Call `service.quick_register(config)` — it registers all factor definitions and binds `ColumnExtractLogic` to each
4. Call `service.compute_and_store(...)` per symbol to fetch and persist values

## QuickRegisterConfig

```python
from src.trading_system.factors.quick_register import QuickRegisterConfig

QuickRegisterConfig(
    data_source="tushare_daily",       # must match a registered DataSourceConfig name
    fields=["open", "high", "low", "close", "vol"],  # columns to extract
    prefix="daily_",                   # prepended to each field name
    category="TuShareDaily",           # factor category tag
    description_template="Daily bar factor: {field}",  # {field} is substituted
)
```

Registered factor names will be: `daily_open`, `daily_high`, `daily_low`, `daily_close`, `daily_vol`.

If `fields` is omitted, all numeric columns (excluding identifier columns like `ts_code`, `trade_date`, `symbol`, `timestamp`) are auto-detected.

## Full Example

```python
from src.trading_system.factors.config import DataSourceConfig
from src.trading_system.factors.quick_register import QuickRegisterConfig
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.time_resolver import TimeRangeResolver
from src.trading_system.factors.settings import DB_PATH, TUSHARE_TOKEN

# 1. Define data source
ds_config = DataSourceConfig(
    name="tushare_daily",
    source_class="TuShareDataSource",
    params={"api": "daily", "symbols": ["000001.SZ"], "token": TUSHARE_TOKEN},
    time_range={"start": "today-365d", "end": "today"},
)

# 2. Define quick register
qr_config = QuickRegisterConfig(
    data_source="tushare_daily",
    fields=["open", "high", "low", "close", "vol", "amount"],
    prefix="daily_",
    category="TuShareDaily",
)

# 3. Register and ingest
db = FactorDatabase(DB_PATH)
svc = FactorService(db)
factor_names = svc.quick_register(qr_config)  # registers factor definitions
print(f"Registered: {factor_names}")

start = TimeRangeResolver.resolve("today-365d")
end   = TimeRangeResolver.resolve("today")

for factor_name in factor_names:
    svc.compute_and_store("000001.SZ", factor_name, "tushare_daily", start, end)
```

## Using the Built-in Task Scripts

The simplest way is to use the ready-made extension scripts. Edit `SYMBOLS` and run:

```bash
# Daily bars
python -m src.trading_system.factors.extensions.tushare_daily_task

# Daily basic indicators
python -m src.trading_system.factors.extensions.tushare_basic_task
```

To create tasks for your own symbol, copy the template files:

```bash
# Templates with placeholder symbols
src/trading_system/factors/extensions/tushare_daily_task_X.py   # edit SYMBOLS = ["your_code"]
src/trading_system/factors/extensions/tushare_basic_task_Y.py   # edit SYMBOLS = ["your_code"]
```

## Auto-detected Columns

When `fields` is not specified, `QuickRegisterConfig` calls `detect_factor_columns(df)` which returns all numeric columns excluding these identifier columns:

```python
IDENTIFIER_COLUMNS = {'ts_code', 'trade_date', 'symbol', 'timestamp', 'date', 'code'}
```

## Querying Registered Factors

```python
values = svc.get_factor_values(
    "000001.SZ", "daily_close",
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2026, 1, 1),
)
for v in values:
    print(v.timestamp, v.value)
```
