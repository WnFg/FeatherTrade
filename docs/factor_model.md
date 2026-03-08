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

## 5. 配置驱动注册（推荐方式）

除了上述编程式注册，系统支持通过声明式配置自动注册因子、数据源和调度任务。

**重要说明**：
- **因子计算逻辑（`BaseFactorLogic` 子类）必须用 Python 代码定义** — 这是因子的核心部分
- **因子元数据、数据源、调度任务可以用配置定义** — 减少样板代码

### 5.1 配置数据结构

三个核心 dataclass 定义在 `src/trading_system/factors/config.py`：

- `FactorConfig` — 因子元数据（name, category, display_name, formula_config, version）
- `DataSourceConfig` — 数据源配置（name, source_class, params, time_range, transformation）
- `ScheduleConfig` — 调度任务配置（name, factor, data_source, trigger, is_active）

### 5.2 Python 配置方式

在 `factors/extensions/` 目录下创建 `.py` 文件，定义模块级变量：

```python
from src.trading_system.factors.base import BaseFactorLogic
from src.trading_system.factors.config import FactorConfig, DataSourceConfig, ScheduleConfig

# 1. 定义计算逻辑（必须用代码）
class PERatioFactor(BaseFactorLogic):
    def compute(self, data):
        if 'pe' not in data.columns or data.empty:
            return None
        return data['pe'].iloc[-1]

# 2. 定义元数据配置
FACTOR_CONFIGS = [
    FactorConfig(
        name="peratioFactor",  # 必须与类名小写一致
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

### 5.3 YAML 配置方式

**限制**：YAML 只能定义配置，不能定义计算逻辑。必须配合 Python 文件定义 `BaseFactorLogic` 子类。

等价的 YAML 文件（放在 `factors/extensions/` 目录下）：

```yaml
factor_configs:
  - name: peratioFactor  # 必须与 Python 文件中的类名小写一致
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

### 5.4 自动发现机制

`DiscoveryEngine` 在 `FactorService` 初始化时自动扫描 `builtin/` 和 `extensions/` 目录：
- Python 文件中的 `FACTOR_CONFIGS`、`DATA_SOURCE_CONFIGS`、`SCHEDULE_CONFIGS` 变量
- `.yaml` 文件中的 `factor_configs`、`data_source_configs`、`schedule_configs` 节
- `BaseFactorLogic` 和 `BaseDataSource` 子类

扫描结果自动注册到 `FactorRegistry`，无需手动调用注册方法。

### 5.5 相对时间范围

`DataSourceConfig.time_range` 支持相对时间表达式，在调度执行时动态解析：
- `today` — 当天 00:00:00
- `today-Nd` — N 天前（如 `today-3d`）
- `today-Nw` — N 周前（如 `today-1w`）
- ISO 8601 格式 — 固定日期（如 `2024-01-01`）
