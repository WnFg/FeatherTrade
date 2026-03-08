# Factor Config Guide

This guide covers the three configuration dataclasses used to extend the factor system: `FactorConfig`, `DataSourceConfig`, and `ScheduleConfig`.

## Overview

Config-driven extension is the recommended approach for adding factors, data sources, and scheduled tasks:

- **Lightweight** — no changes to framework code; just add a file to `extensions/`
- **Declarative** — config doubles as documentation
- **Auto-discovered** — placed in `extensions/`, loaded automatically on `FactorService` init
- **Decoupled** — user code is fully separated from framework internals

> **Important**: Factor computation logic (`BaseFactorLogic` subclasses) must be defined in Python code.
> Factor metadata, data sources, and schedules can be defined via config.

---

## FactorConfig

Defines factor metadata. Maps to a row in the `factor_definitions` table.

```python
@dataclass
class FactorConfig:
    name: str                           # unique factor identifier (required)
    category: str                       # e.g. Value, Momentum, Volatility
    display_name: Optional[str] = None  # human-readable name
    formula_config: Dict[str, Any] = field(default_factory=dict)  # params passed to compute()
    version: str = "1.0.0"
    description: Optional[str] = None
```

**Example**:

```python
# Step 1: define computation logic (required in code)
class PERatioFactor(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: dict) -> pd.DataFrame:
        return pd.DataFrame({
            "timestamp": data["timestamp"],
            "symbol":    data["symbol"],
            "value":     data["pe"].astype(float),
        })

# Step 2: define metadata
FACTOR_CONFIGS = [
    FactorConfig(
        name="peratioFactor",   # must match class name lowercased
        category="Value",
        display_name="PE Ratio",
        formula_config={"field": "pe"},
        description="Price-to-earnings ratio from TuShare daily_basic"
    )
]
```

---

## DataSourceConfig

Defines a data source instance including class, parameters, time range, and column transformations.

```python
@dataclass
class DataSourceConfig:
    name: str                           # instance name (required)
    source_class: str                   # class name, e.g. "TuShareDataSource" (required)
    params: Dict[str, Any] = field(default_factory=dict)  # passed to configure()
    time_range: Optional[Dict[str, str]] = None           # {start, end}
    transformation: Optional[Dict[str, Any]] = None       # rename/type_casting rules
```

**Parameters**:
- `source_class` — simple class name (auto-resolved from builtins and extensions) or full dotted path
- `params.symbols` — list of stock codes; expanded per-symbol at execution time
- `time_range` — supports relative expressions (see below)
- `transformation` — column rename and type-cast rules applied after `fetch_data`

**Example**:

```python
DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_daily_basic",
        source_class="TuShareDataSource",
        params={
            "api": "daily_basic",
            "symbols": ["000001.SZ", "600000.SH"],
            "fields": ["pe", "pb", "ps"]
        },
        time_range={"start": "today-7d", "end": "today"},
        transformation={
            "rename": {"ts_code": "symbol", "trade_date": "timestamp"},
            "type_casting": {"pe": "float", "pb": "float"}
        }
    )
]
```

### Relative Time Ranges

| Expression | Meaning |
|---|---|
| `today` | Today at 00:00:00 |
| `today-Nd` | N days ago (e.g. `today-3d`) |
| `today-Nw` | N weeks ago (e.g. `today-1w`) |
| `2025-01-01` | Fixed ISO 8601 date |
| `2025-01-01T10:00:00` | Fixed ISO 8601 datetime |

Expressions are resolved at job execution time, so `today-7d` always means "7 days before the run".

### Transformation Rules

```python
transformation={
    "rename": {
        "ts_code":    "symbol",     # rename TuShare column to framework standard
        "trade_date": "timestamp"
    },
    "type_casting": {
        "pe":     "float",
        "volume": "int"
    }
}
```

---

## ScheduleConfig

Defines a scheduled ingestion task linking a factor to a data source.

```python
@dataclass
class ScheduleConfig:
    name: str                           # job name (required)
    factor: str                         # factor name (required)
    data_source: str                    # data source name (required)
    trigger: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
```

### Trigger Types

**Cron** — recurring on a schedule:
```python
trigger={"type": "cron", "expr": "0 18 * * 1-5"}   # weekdays at 18:00
```

**Interval** — recurring every N seconds:
```python
trigger={"type": "interval", "seconds": 3600}        # every hour
```

**One-off** — run once at a specific time:
```python
trigger={"type": "one-off", "run_time": "2025-06-01T18:00:00"}
```

**Example**:

```python
SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_job",
        factor="peratioFactor",
        data_source="tushare_daily_basic",
        trigger={"type": "cron", "expr": "0 18 * * 1-5"},
        is_active=True
    )
]
```

---

## Auto-Discovery

`FactorService` scans `builtin/` and `extensions/` on init:

1. Imports all `.py` files and looks for `FACTOR_CONFIGS`, `DATA_SOURCE_CONFIGS`, `SCHEDULE_CONFIGS` variables
2. Parses all `.yaml` files for `factor_configs`, `data_source_configs`, `schedule_configs` sections
3. Discovers `BaseFactorLogic` and `BaseDataSource` subclasses

All discovered items are registered to `FactorRegistry` automatically.

---

## Best Practices

- **Naming**: use `snake_case` for factor names; data source names should be descriptive (e.g. `tushare_daily_basic`)
- **Scheduling**: avoid running all jobs at exactly `:00` — stagger by a few minutes to avoid API rate limits
- **TuShare rate limits**: leave at least 5 minutes between jobs that call the same API
- **Incremental updates**: use `today-1d` to `today` for daily refresh; use fixed dates for historical backfill
- **Idempotency**: `FactorConfig` registration is upsert — safe to restart without creating duplicates

---

## Reference

| File | Purpose |
|---|---|
| `src/trading_system/factors/config.py` | Dataclass definitions |
| `src/trading_system/factors/time_resolver.py` | Relative time expression parser |
| `src/trading_system/factors/registry.py` | Config scanning and registration logic |
| `src/trading_system/factors/scheduler.py` | Scheduled task execution |
| `src/trading_system/factors/extensions/example_value_factors.py` | Full working example |
