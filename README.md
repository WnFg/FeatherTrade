# FeatherTrade

An event-driven trend trading framework for A-share quantitative research. **FeatherTrade** is lightweight, modular, and built for both researchers and developers. Supports strategy development, backtesting, and a factor management pipeline for building and persisting financial factors from external data sources.

---

## Features

- **Event-driven core** — all components communicate via a typed event queue; same interfaces work in backtest and live modes
- **Strategy framework** — implement `on_bar` / `on_tick`, emit signals, plug in risk rules
- **Backtest simulator** — replays bar data, fills orders at close price, tracks cash and positions
- **Risk management** — pluggable stop-loss / take-profit rules evaluated on every market event
- **Factor system** — fetch, compute, and persist financial factors to SQLite; extensible via drop-in Python files
- **TuShare integration** — built-in `TuShareDataSource` for A-share daily bars and daily_basic indicators
- **Quick register** — register a full set of factors from a DataFrame API in one config block

---

## Quick Start

### Requirements

- Python 3.10+
- `pip install tushare apscheduler pyyaml pandas`

### Configuration

Copy the workspace config template and fill in your TuShare token:

```bash
cp workspace/config/factors.yaml.example workspace/config/factors.yaml
# edit workspace/config/factors.yaml: set tushare_token
```

Or set via environment variable:

```bash
export TUSHARE_TOKEN=your_token_here
```

### Run a backtest (CSV data)

```bash
python run_backtest.py
python run_risk_backtest.py
```

### Run a backtest (factor database)

```bash
# 1. Pull data into the factor DB first
python -m src.trading_system.factors.extensions.tushare_daily_task

# 2. Run the factor-powered backtest
python run_factor_backtest.py
```

---

## Documentation

| Document | Description |
|---|---|
| [Strategy Guide](docs/策略机制.md) | How to write strategies and connect them to the backtest engine |
| [Factor System Overview](docs/factor_model.md) | Factor pipeline architecture: fetch → compute → store |
| [Factor Quick Register](docs/因子快捷注册.md) | Batch-register factors from a data source in one config block |
| [TuShare Data Source](docs/tuShare数据源.md) | Using `TuShareDataSource` for A-share data ingestion |
| [User Data Source & Factor Examples](docs/用户注册数据源与因子用例.md) | Step-by-step examples for registering data sources and factors |
| [Extensibility & Scheduling](docs/factor_extensibility_scheduling.md) | Extension pattern and scheduled ingestion tasks |
| [Extension Guide](docs/extension-guide.md) | How to extend strategies, adapters, and factor components |
| [Architecture](docs/architecture.md) | System architecture and event flow |
| [Goals](docs/goals.md) | Design goals and non-goals |

---

## Architecture Overview

```
CSVDataFeed / FactorDataFeed
  → MarketEvent
    → StrategyManager → Strategy.on_bar()
      → SignalEvent
        → BacktestSimulator / ExecutionEngine
          → FillEvent
            → AccountService (cash & positions)
              → RiskManager → RiskSignalEvent (stop-loss / take-profit)
```

### Package Structure

```
src/trading_system/
├── core/           # EventEngine, StrategyManager, BacktestRunner
├── data/           # Bar, Tick domain models
├── modules/        # CSVDataFeed, FactorDataFeed, BacktestSimulator,
│                   # AccountService, ExecutionEngine
├── strategies/     # BaseStrategy, StatefulStrategy, built-in strategies
├── risk/           # RiskManager, BaseRiskStrategy, FixedStopLoss/TakeProfit
└── factors/        # Factor pipeline
    ├── builtin/    # FileDataSource, APIDataSource, TuShareDataSource
    │               # MovingAverageFactor, ColumnExtractLogic
    ├── extensions/ # Drop user extensions here (auto-discovered)
    └── ...         # FactorService, FactorRegistry, TaskScheduler, FactorDatabase
```

---

## Writing a Strategy

Subclass `BaseStrategy` (or `StatefulStrategy` for state-machine / stop-loss support):

```python
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.strategies.context import StrategyContext

class MyStrategy(BaseStrategy):
    def on_bar(self, bar: Bar, context: StrategyContext):
        # Access account state
        cash = context.account.cash

        # Emit a buy signal (100 shares at market price)
        self.send_signal(bar.symbol, "BUY", 100, bar.close)

    def on_tick(self, tick: Tick, context: StrategyContext):
        pass  # tick-level logic (optional)
```

See [Strategy Guide](docs/策略机制.md) for the full `StatefulStrategy` API including ATR stop-loss and position sizing.

---

## Running a Backtest

```python
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.strategy_manager import StrategyManager
from src.trading_system.modules.backtest_simulator import BacktestSimulator
from src.trading_system.modules.account_service import AccountService
from src.trading_system.modules.csv_data_feed import CSVDataFeed

engine          = EventEngine()
account_service = AccountService(engine, initial_cash=500_000)
simulator       = BacktestSimulator(engine, account_service)
manager         = StrategyManager(engine, simulator, account_service=account_service)

strategy = MyStrategy(engine, {"fast_period": 10, "slow_period": 30})
manager.add_strategy(strategy)

feed = CSVDataFeed(engine, symbol="000001.SZ", file_path="data/000001.csv")

engine.start()
feed.start()
# ... wait for feed to finish ...
feed.stop()
engine.stop()
```

To use factor DB data instead of CSV, replace `CSVDataFeed` with `FactorDataFeed` — see `run_factor_backtest.py`.

---

## Factor Management

### Pulling data and registering factors (one command)

Edit the `SYMBOLS` variable in the extension file, then run:

```bash
# A-share daily bars (open, high, low, close, vol, ...)
python -m src.trading_system.factors.extensions.tushare_daily_task

# Daily basic indicators (PE, PB, turnover rate, market cap, ...)
python -m src.trading_system.factors.extensions.tushare_basic_task
```

### Using factors in a strategy

```python
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.settings import DB_PATH
from datetime import datetime

db  = FactorDatabase(DB_PATH)
svc = FactorService(db)

values = svc.get_factor_values(
    "000001.SZ", "daily_close",
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2026, 1, 1),
)
for v in values:
    print(v.timestamp, v.value)
```

---

## For Advanced Users

### Adding a custom factor

Drop a `.py` file in `src/trading_system/factors/extensions/` with a class inheriting `BaseFactorLogic`:

```python
import pandas as pd
from typing import Dict, Any
from src.trading_system.factors.base import BaseFactorLogic

class MyFactor(BaseFactorLogic):
    def compute(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        window = config.get("window", 20)
        return pd.DataFrame({
            "timestamp": data["timestamp"],
            "symbol":    data["symbol"],
            "value":     data["close"].rolling(window).mean(),
        })
```

It is auto-discovered at `FactorService` init — no registration code needed.

### Adding a custom data source

```python
from src.trading_system.factors.base import BaseDataSource
import pandas as pd
from datetime import datetime

class MyDataSource(BaseDataSource):
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        # return DataFrame with at least: timestamp/trade_date, symbol/ts_code, and value columns
        ...
```

### Quick-registering factors from a new data source

```python
from src.trading_system.factors.config import DataSourceConfig
from src.trading_system.factors.quick_register import QuickRegisterConfig

DATA_SOURCE_CONFIGS = [
    DataSourceConfig(
        name="my_source",
        source_class="MyDataSource",
        params={"api": "my_api", "symbols": ["600519.SH"]},
        time_range={"start": "today-365d", "end": "today"},
    )
]

QUICK_REGISTER_CONFIGS = [
    QuickRegisterConfig(
        data_source="my_source",
        fields=["open", "close", "pe"],
        prefix="my_",
        category="MyCategory",
    )
]
```

See [Extensibility & Scheduling](docs/factor_extensibility_scheduling.md) for scheduled ingestion (cron / one-off tasks via APScheduler).

### Adding a custom risk rule

```python
from src.trading_system.risk.base_risk import BaseRiskStrategy
from src.trading_system.modules.execution_engine import Position

class MyRiskRule(BaseRiskStrategy):
    def evaluate(self, position: Position, current_price: float):
        threshold = self._params.get("threshold", 0.05)
        if position.quantity > 0:
            loss_pct = (position.average_cost - current_price) / position.average_cost
            if loss_pct >= threshold:
                return "SELL_ALL"
        return None

# Attach to RiskManager:
risk_manager.add_strategy(MyRiskRule({"threshold": 0.05}))
```

---

## Running Tests

```bash
python -m pytest tests/
python -m pytest tests/unit/
python -m pytest tests/integration/
```

---

## Built-in Strategies

| Strategy | Description |
|---|---|
| `MovingAverageCrossover` | Simple MA crossover (fast/slow) |
| `AtrTrendStrategy` | ATR-based trend following with volatility stop |
| `DualMATrendStrategy` | Dual MA + 60-day trend filter + ATR stop, A-share sizing |

---

## License

MIT
