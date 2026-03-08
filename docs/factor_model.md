# Financial Factor Model Design & Implementation

This document outlines the design and current implementation for representing and storing financial factors in the trading system using SQLite.

## 1. Conceptual Model

The factor system is split into two primary layers:
- **Metadata Layer**: Defines what a factor is, its parameters, and its version.
- **Data Layer**: Stores the actual time-series values computed for specific symbols.

### Key Principles
- **Extensibility**: New factors are "data, not code" at the database level. Add new logic by implementing `BaseFactorLogic`.
- **Efficiency**: Optimized for time-series retrieval. Supports batch calculation and storage.
- **Pluggability**: Data sources (`BaseDataSource`) and calculation logic are decoupled from the core service.

## 2. SQLite Schema Definition

Implemented in `src/trading_system/factors/schema.sql`.

```sql
CREATE TABLE IF NOT EXISTS factor_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,          
    display_name TEXT,                  
    category TEXT,                      
    description TEXT,                   
    formula_config TEXT,                -- JSON: {"window": 20, "price_key": "close"}
    version TEXT DEFAULT '1.0.0',       
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS factor_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_id INTEGER NOT NULL,         
    symbol TEXT NOT NULL,               
    timestamp DATETIME NOT NULL,        
    value REAL NOT NULL,                
    metadata TEXT,                      
    FOREIGN KEY (factor_id) REFERENCES factor_definitions(id) ON DELETE CASCADE
);
```

## 3. Python API Usage

### 3.1 Setup and Registration

```python
from trading_system.factors.database import FactorDatabase
from trading_system.factors.service import FactorService, MovingAverageFactor, FileDataSource
from trading_system.factors.models import FactorDefinition

db = FactorDatabase("factors.db")
service = FactorService(db)

# Register a new factor definition
defn = FactorDefinition(
    id=None, name="sma_20", display_name="SMA (20)", 
    category="Momentum", description="Simple Moving Average",
    formula_config={"window": 20}
)
service.registry.register_factor(defn)

# Register logic and data source
service.register_logic("sma_20", MovingAverageFactor())
service.register_source("local_csv", FileDataSource("data.csv"))
```

### 3.2 Computation and Querying

```python
# Compute factors from a data source and store in DB
service.compute_and_store(
    symbol="AAPL", 
    factor_name="sma_20", 
    source_name="local_csv",
    start_time=datetime(2023, 1, 1), 
    end_time=datetime(2023, 12, 31)
)

# Retrieve stored factor values
values = service.get_factor_values("AAPL", "sma_20", limit=10)

# Batch retrieve by category
momentum_factors = service.get_factor_values_by_category("AAPL", "Momentum")
```

## 4. Extending the System

To add a new factor:
1. Inherit from `BaseFactorLogic` and implement `compute()`.
2. Register the new logic class with `FactorService.register_logic()`.
3. Add a matching entry in `factor_definitions` (via code or SQL).

## 5. Config-Driven Registration (Recommended)

In addition to the programmatic approach above, the system supports declarative config-based registration for factors, data sources, and scheduled tasks.

**Key point**:
- **Factor computation logic (`BaseFactorLogic` subclasses) must be defined in Python code** — this is the core of a factor
- **Factor metadata, data sources, and schedules can be defined via config** — reducing boilerplate

### 5.1 Config Data Structures

Three core dataclasses defined in `src/trading_system/factors/config.py`:

- `FactorConfig` — factor metadata (name, category, display_name, formula_config, version)
- `DataSourceConfig` — data source config (name, source_class, params, time_range, transformation)
- `ScheduleConfig` — scheduled task config (name, factor, data_source, trigger, is_active)

### 5.2 Python Config

Create a `.py` file in `factors/extensions/` with module-level variables:

```python
from src.trading_system.factors.base import BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig

# 1. Define computation logic (must be code)
class PERatioFactor(BaseFactorLogic):
    def compute(self, data, config):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]

# 2. Define metadata config
FACTOR_CONFIGS = [
    FactorConfig(
        name="peratioFactor",  # must match class name (lowercased)
        category="Value",
        display_name="PE Ratio",
        formula_config={"field": "pe"}
    )
]

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="tushare_daily_basic",
        source_class="TuShareDataSource",
        params={"api": "daily_basic", "symbols": ["000001.SZ"], "fields": ["pe", "pb"]},
        time_range={"start": "today-3d", "end": "today"},
        transformation={"rename": {"ts_code": "symbol", "trade_date": "timestamp"}}
    )
]

SCHEDULE_CONFIGS = [
    ScheduleConfig(
        name="daily_pe_job",
        factor="peratioFactor",
        data_source="tushare_daily_basic",
        trigger={"type": "cron", "expr": "0 18 * * 1-5"}
    )
]
```

### 5.3 YAML Config

**Limitation**: YAML can only define config, not computation logic. Must be paired with a Python file defining `BaseFactorLogic` subclasses.

Equivalent YAML file (placed in `factors/extensions/`):

```yaml
factor_configs:
  - name: peratioFactor  # must match Python class name (lowercased)
    category: Value
    display_name: PE Ratio
    formula_config:
      field: pe

data_source_configs:
  - name: tushare_daily_basic
    source_class: TuShareDataSource
    params:
      api: daily_basic
      symbols: ["000001.SZ"]
    time_range:
      start: today-3d
      end: today

schedule_configs:
  - name: daily_pe_job
    factor: pe_ratio
    data_source: tushare_daily_basic
    trigger:
      type: cron
      expr: "0 18 * * 1-5"
```

### 5.4 Auto-Discovery

`DiscoveryEngine` scans `builtin/` and `extensions/` directories on `FactorService` init:
- `FACTOR_CONFIGS`, `DATA_SOURCE_CONFIGS`, `SCHEDULE_CONFIGS` variables in Python files
- `factor_configs`, `data_source_configs`, `schedule_configs` sections in `.yaml` files
- `BaseFactorLogic` and `BaseDataSource` subclasses

All discovered configs are automatically registered to `FactorRegistry` — no manual registration calls needed.

### 5.5 Relative Time Ranges

`DataSourceConfig.time_range` supports relative time expressions, resolved dynamically at execution time:
- `today` — today at 00:00:00
- `today-Nd` — N days ago (e.g. `today-3d`)
- `today-Nw` — N weeks ago (e.g. `today-1w`)
- ISO 8601 format — fixed date (e.g. `2024-01-01`)
