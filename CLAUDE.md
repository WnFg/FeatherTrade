# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/unit/test_factor_system.py

# Run a single test case
python -m pytest tests/unit/test_factor_system.py::TestFactorSystem::test_factor_registration

# Run integration tests
python -m pytest tests/integration/
```

The project has no build step — it is pure Python. The source package is under `src/` and imports use `src.trading_system.*` paths directly (no editable install required, just run from the repo root).

### Running a Backtest
```bash
python run_backtest.py
python run_risk_backtest.py
```

## Architecture

This is an **event-driven trend trading system** built around a central `EventEngine`. All components communicate exclusively via typed events dispatched through a single queue.

### Event Flow
```
CSVDataFeed / SignalModule
  → MarketEvent
    → StrategyManager → Strategy.on_bar()
      → SignalEvent
        → ExecutionEngine / BacktestSimulator
          → OrderEvent → FillEvent
            → AccountService (updates cash & positions)
              → RiskManager (evaluates stop-loss / take-profit)
                → RiskSignalEvent (triggers close orders)
```

### Core Packages

| Package | Responsibility |
|---|---|
| `core/` | `EventEngine` (threaded queue + dispatch), `StrategyManager`, `BacktestRunner` |
| `modules/` | `CSVDataFeed`, `BacktestSimulator`, `ExecutionEngine`, `AccountService`, `SignalModule` |
| `strategies/` | `BaseStrategy` (abstract), `StatefulStrategy`, `MovingAverageCrossover`, `AtrTrendStrategy` |
| `risk/` | `RiskManager`, `BaseRiskStrategy`, `FixedStopLossStrategy`, `FixedTakeProfitStrategy` |
| `data/` | Domain models: `Bar`, `Tick`, `Order`, `Position` |
| `factors/` | Factor computation pipeline (see below) |

### Factor System (`factors/`)

A separate sub-system for computing and persisting financial factors, independent of the backtest event loop.

- **`FactorService`** — main entry point; coordinates fetch → transform → compute → store
- **`FactorRegistry`** + **`DiscoveryEngine`** — auto-discovers `BaseFactorLogic` and `BaseDataSource` subclasses from `builtin/` and `extensions/` directories via `importlib`; extensions override builtins for unprefixed names
- **`DataSourceFactory`** — instantiates data sources from a `class_path` string + parameters dict (stored in DB)
- **`ParameterTransformer`** — applies column rename/type-cast transformations defined in `DataSourceInstance.transformation_config` or `DataSourceConfig.transformation`
- **`TaskScheduler`** — wraps APScheduler; persists jobs to SQLite; supports `cron`, `interval`, and `one-off` triggers; supports both DB-driven (`ScheduledTask`) and config-driven (`ScheduleConfig`) task execution
- **`FactorDatabase`** — thin SQLite wrapper for `factor_definitions`, `factor_values`, `data_source_instances`, `scheduled_tasks`, and `task_execution_logs`

**Config-driven extension (recommended)**: drop a `.py` or `.yaml` file in `factors/extensions/` with `FACTOR_CONFIGS`, `DATA_SOURCE_CONFIGS`, `SCHEDULE_CONFIGS` module-level variables (Python) or equivalent YAML keys. These are auto-discovered and registered on `FactorService` init.

**Config dataclasses** (`factors/config.py`):
- `FactorConfig` — factor metadata (name, category, formula_config, version)
- `DataSourceConfig` — data source instance (source_class, params with symbols list, time_range with relative expressions, transformation rules)
- `ScheduleConfig` — scheduled task (factor, data_source, trigger type/expr)

**Time range resolver** (`factors/time_resolver.py`): resolves relative expressions like `today-3d`, `today-1w` at execution time.

**Class extension pattern**: drop a `.py` file in `factors/extensions/` containing a class that subclasses `BaseFactorLogic` or `BaseDataSource`. It is auto-discovered on `FactorService` init — no registration code needed. `BaseDataSource` subclasses should implement `configure(params)` for parameter injection.

**Builtin components**:
- `builtin/factors.py` — `MovingAverageFactor` (SMA)
- `builtin/data_sources.py` — `FileDataSource` (CSV), `APIDataSource` (skeleton), `TuShareDataSource` (requires `tushare` + `TUSHARE_TOKEN` env var)

**Data source resolution priority**: (1) `DataSourceConfig` from registry → (2) `DataSourceInstance` from DB → (3) dynamic class registry

See `docs/factor_config_guide.md` for detailed usage guide with TuShare PE/PB example.

### Strategy Interface

Subclass `BaseStrategy` and implement `on_tick(tick, context)` and `on_bar(bar, context)`. Call `self.send_signal(symbol, side, quantity, price)` to emit a `SignalEvent`. Strategies receive a `StrategyContext` object with account state.

### Key Design Constraints

- The same `BaseStrategy` / `ExecutionEngine` interfaces are used in both live and backtest modes — do not add backtest-only branches inside strategies.
- `EventEngine` runs in a background thread; handlers must be thread-safe.
- `FactorService` has a simple in-memory cache keyed by `symbol:factor_name:start:end:limit` — call `clear_cache()` after writes if stale reads are a concern.
