# Documentation Index

## Quick Navigation

### Getting Started

| Document | Description |
|---|---|
| [Architecture](architecture.md) | Event-driven architecture, module responsibilities, event flow |
| [Goals](goals.md) | Design principles and non-goals |

### Strategy Development & Backtesting

| Document | Description |
|---|---|
| [Strategy Guide](strategy-guide.md) | BaseStrategy / StatefulStrategy API, `on_bar` / `on_tick`, signal emission, state machine, risk hooks |
| [Extension Guide](extension-guide.md) | How to extend strategies, data adapters, and execution adapters |

### Factor Management

| Document | Description |
|---|---|
| [Factor Model](factor_model.md) | Factor pipeline architecture: fetch → transform → compute → store |
| [Factor Quick Register](factor-quick-register.md) | `QuickRegisterConfig` — batch-register factors from a data source in one config block |
| [Factor Extension Examples](factor-extension-examples.md) | End-to-end examples: register custom factors, data sources, and scheduled tasks |
| [TuShare Data Source](tushare-data-source.md) | `TuShareDataSource` setup, `daily` and `daily_basic` API reference |
| [Factor Extensibility & Scheduling](factor_extensibility_scheduling.md) | `extensions/` auto-discovery pattern and APScheduler task configuration |
| [Factor Config Guide](factor_config_guide.md) | Full `FactorConfig` / `DataSourceConfig` / `ScheduleConfig` parameter reference |

---

## Reading Paths

### First-time users

1. Read [Architecture](architecture.md) for a system overview
2. Read [Strategy Guide](strategy-guide.md) to learn how to write strategies
3. Run `run_backtest.py` or `run_factor_backtest.py` for your first backtest

### Users who want external market data

1. Read [TuShare Data Source](tushare-data-source.md) for the built-in data source
2. Read [Factor Quick Register](factor-quick-register.md) to pull and register factors in one command
3. Copy and edit `SYMBOLS` in `src/trading_system/factors/extensions/tushare_daily_task.py`

### Advanced users / framework extenders

1. Read [Factor Extensibility & Scheduling](factor_extensibility_scheduling.md) for the `extensions/` auto-discovery mechanism
2. Read [Factor Extension Examples](factor-extension-examples.md) for the complete extension workflow
3. Read [Extension Guide](extension-guide.md) for strategy and adapter extension interfaces
4. See `src/trading_system/factors/base.py` for `BaseFactorLogic` / `BaseDataSource` interfaces

---

## Example Scripts

| Script | Description |
|---|---|
| `run_backtest.py` | MA crossover strategy backtest using CSV data |
| `run_risk_backtest.py` | Backtest with fixed stop-loss / take-profit risk rules |
| `run_factor_backtest.py` | Dual-MA trend strategy backtest using factor DB data (000001.SZ) |
| `src/.../extensions/tushare_daily_task.py` | Pull A-share daily bars and register as factors |
| `src/.../extensions/tushare_basic_task.py` | Pull daily basic indicators and register as factors |
| `src/.../extensions/tushare_daily_task_X.py` | User template: daily bars for custom symbol |
| `src/.../extensions/tushare_basic_task_Y.py` | User template: daily basic indicators for custom symbol |
