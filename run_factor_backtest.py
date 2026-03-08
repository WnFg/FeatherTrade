"""
000001.SZ 趋势策略回测

使用 DualMATrendStrategy + FactorDataFeed，从因子数据库读取
平安银行(000001.SZ)近一年日线数据执行回测。

执行：
    python run_factor_backtest.py
"""
import time
from datetime import datetime

from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.strategy_manager import StrategyManager
from src.trading_system.modules.backtest_simulator import BacktestSimulator
from src.trading_system.modules.account_service import AccountService
from src.trading_system.modules.factor_data_feed import FactorDataFeed
from src.trading_system.risk.risk_manager import RiskManager
from src.trading_system.risk.fixed_stop_loss import FixedStopLossStrategy
from src.trading_system.strategies.dual_ma_trend_strategy import DualMATrendStrategy
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.settings import DB_PATH


# ── 回测参数 ─────────────────────────────────────────────────────────────────
SYMBOL         = "000001.SZ"
INITIAL_CAPITAL = 500_000.0   # 50万初始资金
START_DATE     = datetime(2025, 3, 10)
END_DATE       = datetime(2026, 3, 8)

STRATEGY_PARAMS = {
    "fast_period":   10,
    "slow_period":   30,
    "trend_period":  60,
    "equity_pct":    0.95,
    "atr_stop_mult": 2.0,
    "atr_period":    14,
}


def run():
    # ── 初始化因子服务 ────────────────────────────────────────────────────────
    db  = FactorDatabase(DB_PATH)
    svc = FactorService(db)

    # ── 检查数据是否就绪 ──────────────────────────────────────────────────────
    sample = svc.get_factor_values(SYMBOL, "daily_close", start_time=START_DATE, end_time=END_DATE)
    if not sample:
        print(f"[ERROR] 因子库中没有 {SYMBOL} daily_close 数据。")
        print("请先运行: python -m src.trading_system.factors.extensions.tushare_daily_task")
        return
    print(f"加载 {SYMBOL} 日线数据: {len(sample)} 个交易日 ({START_DATE.date()} ~ {END_DATE.date()})")

    # ── 搭建回测引擎 ──────────────────────────────────────────────────────────
    engine          = EventEngine()
    account_service = AccountService(engine, initial_cash=INITIAL_CAPITAL)
    simulator       = BacktestSimulator(engine, account_service)
    manager         = StrategyManager(engine, simulator, account_service=account_service)

    # 风控：5% 固定止损兜底（策略内部也有 ATR 止损）
    risk_manager = RiskManager(engine, account_service)
    risk_manager.add_strategy(FixedStopLossStrategy({"stop_loss_pct": 0.05}))

    # ── 数据源：从因子库组装日线 Bar ──────────────────────────────────────────
    feed = FactorDataFeed(
        event_engine=engine,
        symbol=SYMBOL,
        factor_service=svc,
        open_factor="daily_open",
        high_factor="daily_high",
        low_factor="daily_low",
        close_factor="daily_close",
        volume_factor="daily_vol",
        start_time=START_DATE,
        end_time=END_DATE,
    )

    # ── 策略 ─────────────────────────────────────────────────────────────────
    strategy = DualMATrendStrategy(engine, STRATEGY_PARAMS)
    manager.add_strategy(strategy)

    # ── 执行回测 ─────────────────────────────────────────────────────────────
    print("\n--- 开始回测 ---")
    engine.start()
    feed.start()

    while feed._thread and feed._thread.is_alive():
        time.sleep(0.1)
    time.sleep(1)  # 等待剩余事件处理完毕

    feed.stop()
    engine.stop()
    print("--- 回测完成 ---\n")

    # ── 输出结果 ─────────────────────────────────────────────────────────────
    _print_results(account_service, INITIAL_CAPITAL)


def _print_results(account_service, initial_capital: float):
    cash = account_service.cash
    total_value = cash
    positions = account_service._positions

    print("=" * 50)
    print(f"  策略: DualMATrendStrategy  标的: {SYMBOL}")
    print(f"  初始资金: {initial_capital:>12,.2f}")
    print(f"  剩余现金: {cash:>12,.2f}")

    for sym, pos in positions.items():
        if pos.quantity > 0:
            mv = pos.quantity * pos.average_cost
            total_value += mv
            print(f"  持仓: {sym} {pos.quantity} 股 @ 均价 {pos.average_cost:.2f}  市值 ≈ {mv:,.2f}")

    pnl = total_value - initial_capital
    ret = pnl / initial_capital * 100
    print(f"  总资产估值: {total_value:>12,.2f}")
    print(f"  盈亏: {pnl:>+12,.2f}  ({ret:+.2f}%)")
    print("=" * 50)


if __name__ == "__main__":
    run()
