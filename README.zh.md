# FeatherTrade（中文文档）

**FeatherTrade** 是一个面向 A 股量化研究的轻量级事件驱动的交易框架。支持策略开发、历史回测，以及一套完整的因子管理流水线，可从外部数据源拉取、计算并持久化金融因子。

---

## 功能特性

- **事件驱动核心** — 所有组件通过类型化事件队列通信，回测与实盘使用相同接口
- **策略框架** — 实现 `on_bar` / `on_tick`，发送交易信号，插拔式风控规则
- **回测模拟器** — 回放 Bar 数据，以收盘价撮合订单，跟踪现金与持仓
- **回测可视化** — 自动生成含买卖点标注、净值曲线、回撤曲线、持仓量图的交互式 HTML 报告
- **风险管理** — 可插拔的止损 / 止盈规则，每个市场事件均触发评估
- **因子系统** — 拉取、计算并将金融因子持久化至 SQLite；通过放置 Python 文件即可扩展
- **TuShare 集成** — 内置 `TuShareDataSource`，支持 A 股日线行情与每日指标
- **快捷注册** — 一个配置块即可从 DataFrame API 批量注册全套因子

---

## 快速开始

### 环境要求

- Python 3.10+
- `pip install tushare apscheduler pyyaml pandas`

### 配置

复制 workspace 配置模板并填写 TuShare Token：

```bash
cp workspace/config/factors.yaml.example workspace/config/factors.yaml
# 编辑 workspace/config/factors.yaml，填写 tushare_token
```

或通过环境变量设置：

```bash
export TUSHARE_TOKEN=your_token_here
```

### 运行回测（CSV 数据）

```bash
python run_backtest.py
python run_risk_backtest.py
```

回测结束后会自动在项目根目录生成 `backtest_report.html`，用浏览器打开即可查看：
- 价格走势图（叠加买入 ▲ / 卖出 ▼ 标注）
- 资金净值曲线
- 回撤曲线
- 持仓量时序图

**依赖安装**（可视化功能需要）：
```bash
pip install plotly matplotlib pandas numpy
```

也可在代码中手动调用：
```python
result = runner.get_results(save_report=True, report_path="my_report.html")
# 或关闭控制台输出，仅获取结构化结果：
result = runner.get_results(verbose=False)
# result.equity_curve, result.trades, result.metrics ...
```

### 运行回测（因子数据库）

```bash
# 1. 先拉取数据写入因子库
python -m src.trading_system.factors.extensions.tushare_daily_task

# 2. 运行基于因子库的回测
python run_factor_backtest.py
```

---

## 文档索引

| 文档 | 说明 |
|---|---|
| [策略指南](docs/strategy-guide.md) | 如何编写策略并接入回测引擎 |
| [因子系统概览](docs/factor_model.md) | 因子流水线架构：fetch → compute → store |
| [因子快捷注册](docs/factor-quick-register.md) | 一个配置块从数据源批量注册因子 |
| [TuShare 数据源](docs/tushare-data-source.md) | 使用 `TuShareDataSource` 接入 A 股数据 |
| [数据源与因子扩展示例](docs/factor-extension-examples.md) | 注册数据源和因子的完整示例 |
| [可扩展性与调度](docs/factor_extensibility_scheduling.md) | extensions/ 扩展机制与定时任务配置 |
| [扩展指南](docs/extension-guide.md) | 如何扩展策略、适配器与因子组件 |
| [架构概览](docs/architecture.md) | 系统架构与事件流 |
| [设计目标](docs/goals.md) | 设计原则与非目标 |

---

## 架构概览

```
CSVDataFeed / FactorDataFeed
  → MarketEvent
    → StrategyManager → Strategy.on_bar()
      → SignalEvent
        → BacktestSimulator / ExecutionEngine
          → FillEvent
            → AccountService（现金 & 持仓）
              → RiskManager → RiskSignalEvent（止损 / 止盈）
```

### 包结构

```
src/trading_system/
├── core/           # EventEngine、StrategyManager、BacktestRunner
├── data/           # Bar、Tick 领域模型
├── modules/        # CSVDataFeed、FactorDataFeed、BacktestSimulator、
│                   # AccountService、ExecutionEngine
├── strategies/     # BaseStrategy、StatefulStrategy、内置策略
├── risk/           # RiskManager、BaseRiskStrategy、FixedStopLoss/TakeProfit
└── factors/        # 因子流水线
    ├── builtin/    # FileDataSource、APIDataSource、TuShareDataSource
    │               # MovingAverageFactor、ColumnExtractLogic
    ├── extensions/ # 用户扩展目录（自动发现）
    └── ...         # FactorService、FactorRegistry、TaskScheduler、FactorDatabase
```

---

## 编写策略

继承 `BaseStrategy`（或 `StatefulStrategy`，支持状态机 / 止损钩子）：

```python
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.data.market_data import Bar, Tick
from src.trading_system.strategies.context import StrategyContext

class MyStrategy(BaseStrategy):
    def on_bar(self, bar: Bar, context: StrategyContext):
        # 访问账户状态
        cash = context.account.cash

        # 发送买入信号（100 股，市价）
        self.send_signal(bar.symbol, "BUY", 100, bar.close)

    def on_tick(self, tick: Tick, context: StrategyContext):
        pass  # Tick 级别逻辑（可选）
```

完整的 `StatefulStrategy` API（含 ATR 止损、仓位计算）请参考 [策略机制](docs/策略机制.md)。

---

## 运行回测

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
# ... 等待 feed 完成 ...
feed.stop()
engine.stop()
```

如需使用因子数据库替代 CSV，将 `CSVDataFeed` 替换为 `FactorDataFeed`，参考 `run_factor_backtest.py`。

---

## 因子管理

### 一键拉取数据并注册因子

修改扩展文件中的 `SYMBOLS` 变量，然后执行：

```bash
# A 股日线行情（open、high、low、close、vol 等）
python -m src.trading_system.factors.extensions.tushare_daily_task

# 每日指标（PE、PB、换手率、市值等）
python -m src.trading_system.factors.extensions.tushare_basic_task
```

### 在策略中使用因子

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

## 高阶用户扩展

### 添加自定义因子

在 `src/trading_system/factors/extensions/` 目录下放置一个 `.py` 文件，继承 `BaseFactorLogic`：

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

`FactorService` 初始化时自动发现，无需额外注册代码。

### 添加自定义数据源

```python
from src.trading_system.factors.base import BaseDataSource
import pandas as pd
from datetime import datetime

class MyDataSource(BaseDataSource):
    def fetch_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        # 返回至少包含 timestamp/trade_date、symbol/ts_code 以及数值列的 DataFrame
        ...
```

### 从新数据源快捷注册因子

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

定时抓取（cron / 一次性任务，基于 APScheduler）请参考 [可扩展性与调度](docs/factor_extensibility_scheduling.md)。

### 添加自定义风控规则

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

# 挂载到 RiskManager：
risk_manager.add_strategy(MyRiskRule({"threshold": 0.05}))
```

---

## 运行测试

```bash
python -m pytest tests/
python -m pytest tests/unit/
python -m pytest tests/integration/
```

---

## 内置策略

| 策略 | 说明 |
|---|---|
| `MovingAverageCrossover` | 简单均线金叉 / 死叉 |
| `AtrTrendStrategy` | 基于 ATR 的趋势跟踪 + 波动率止损 |
| `DualMATrendStrategy` | 双均线 + 60 日趋势过滤 + ATR 止损，A 股手数整数化仓位 |

---

## 许可证

MIT
