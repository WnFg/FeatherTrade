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
