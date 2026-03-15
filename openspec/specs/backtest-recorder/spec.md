# backtest-recorder Specification

## Purpose
Provides non-intrusive collection of trades and equity data during backtesting by subscribing to EventEngine events. Builds structured BacktestResult objects with performance metrics.

## Requirements

### Requirement: 回测期间无侵入采集成交记录
`BacktestRecorder` SHALL 通过 `EventEngine.register()` 订阅 `EVENT_FILL`，在每次成交时记录 `TradeRecord`（包含 timestamp、symbol、side、quantity、price、pnl）。

#### Scenario: BUY 成交被记录
- **WHEN** 回测运行中触发一个 BUY `FillEvent`
- **THEN** `BacktestRecorder` 的 `trades` 列表中新增一条 `TradeRecord`，side 为 BUY，pnl 为 0.0

#### Scenario: SELL 成交被记录并计算已实现盈亏
- **WHEN** 回测运行中触发一个 SELL `FillEvent`，此前已有对应 BUY 成交
- **THEN** `BacktestRecorder` 的 `trades` 列表中新增一条 `TradeRecord`，side 为 SELL，pnl 为（SELL 价格 - 平均买入成本）× 数量

#### Scenario: 不修改现有模块
- **WHEN** `BacktestRecorder` 被实例化并注册到 `EventEngine`
- **THEN** `AccountService`、`BacktestSimulator`、`StrategyManager` 的代码不发生任何变更

---

### Requirement: 逐 Bar 净值曲线采集
`BacktestRecorder` SHALL 通过 `EventEngine.register()` 订阅 `EVENT_MARKET`，在每根 Bar 结束时计算并记录当前组合净值（现金 + 持仓市值）。

#### Scenario: 净值序列长度等于 Bar 数量
- **WHEN** 回测对 N 根 Bar 完成运行
- **THEN** `equity_curve` 序列的长度为 N

#### Scenario: 无持仓时净值等于现金
- **WHEN** 某根 Bar 处理时持仓数量为 0
- **THEN** 该 Bar 对应的净值等于 `account_service.cash`

#### Scenario: 有持仓时净值含浮盈浮亏
- **WHEN** 某根 Bar 处理时持有 qty 手，Bar 收盘价为 close_price
- **THEN** 该 Bar 对应的净值为 `account_service.cash + qty × close_price`

---

### Requirement: 构建结构化回测结果对象
`BacktestRecorder.build_result()` SHALL 汇总所有采集数据，返回 `BacktestResult` 对象，包含：成交记录列表、净值序列、回撤序列、持仓量序列、所有历史 Bar、绩效指标字典（total_return、max_drawdown、sharpe_ratio、win_rate）。

#### Scenario: 正常回测后生成完整结果
- **WHEN** 回测运行结束后调用 `build_result()`
- **THEN** 返回的 `BacktestResult` 中 `equity_curve`、`drawdown_curve`、`position_curve` 长度相同，`trades` 列表非空（若有成交），`metrics` 字典包含 total_return、max_drawdown、sharpe_ratio、win_rate 四个键

#### Scenario: 零成交时仍可构建结果
- **WHEN** 回测期间无任何成交
- **THEN** `build_result()` 正常返回，`trades` 为空列表，净值曲线为常数（等于初始资金）
