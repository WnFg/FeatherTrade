# Architectural Blueprint

## Design Principles
- **Event-Driven**: All components communicate via events dispatched by a central `EventEngine`.
- **Modular and Decoupled**: Each module (Signal, Strategy, Execution) is independent and connects via standard interfaces.
- **Backtest Fidelity**: The same strategy and execution interfaces are used in both live and simulation modes to ensure backtest results are reliable.

## Core Architectural Components

### Event Engine
The `EventEngine` manages a queue of events (Market, Signal, Order, Fill) and dispatches them to registered callback handlers.

### Module Interactions
- **Signal Modules**: Ingest market data (e.g., CSV, REST API) and produce `MarketEvents`.
- **Strategy Manager**: Dispatches `MarketEvents` to loaded strategies.
- **Strategy Modules**: Evaluate logic and generate `SignalEvents`.
- **Execution Manager**: Converts `SignalEvents` into `OrderEvents`.
- **Executors/Simulators**: Process `OrderEvents` and generate `FillEvents`.

## Domain Models
Defined in `src/trading_system/data/` and `src/trading_system/modules/execution_engine.py`.

| Model | Purpose | Key Attributes |
|---|---|---|
| `Tick` | Represents a single trade or quote. | symbol, timestamp, price, volume |
| `Bar` | Represents an OHLCV candle. | symbol, timestamp, open, high, low, close, volume |
| `Order` | Represents a request to trade. | order_id, symbol, side, type, quantity, price, status |
| `Position` | Tracks current asset holdings. | symbol, quantity, average_cost |

## Engineering Structure
- `src/trading_system/core/`: Event engine, strategy manager, and core framework utilities.
- `src/trading_system/modules/`: Signal modules (e.g., `CSVDataFeed`) and execution engines.
- `src/trading_system/strategies/`: Concrete strategy implementations and `BaseStrategy` interface.
- `src/trading_system/data/`: Data models and market data utilities.
- `tests/`: Unit and integration test suites.
