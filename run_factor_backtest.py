"""
000001.SZ 趋势策略回测

使用 DualMATrendStrategy + FactorDataFeed，从因子数据库读取
平安银行(000001.SZ)近一年日线数据执行回测。

执行：
    python run_factor_backtest.py

可选参数：
    --no-report   跳过生成 HTML 可视化报告
    --png         生成 PNG 格式报告（默认 HTML）
"""
import argparse
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
from src.trading_system.backtest.recorder import BacktestRecorder
from src.trading_system.backtest.visualizer import BacktestVisualizer


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


def run(save_report: bool = True, report_fmt: str = "html"):
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

    # ── 录制器（收集权益曲线、成交记录等） ───────────────────────────────────
    recorder = BacktestRecorder(engine, account_service, SYMBOL, INITIAL_CAPITAL)

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

    # ── 构建结果 ─────────────────────────────────────────────────────────────
    result = recorder.build_result()

    # ── 输出文字结果 ─────────────────────────────────────────────────────────
    _print_results(result, account_service)

    # ── 可视化报告 ───────────────────────────────────────────────────────────
    if save_report:
        report_ext  = "png" if report_fmt == "png" else "html"
        report_path = f"factor_backtest_report.{report_ext}"
        visualizer  = BacktestVisualizer()
        visualizer.plot(result, output_path=report_path)
        print(f"\n  [可视化] 报告已保存至: {report_path}")

    return result


def _print_results(result, account_service):
    from src.trading_system.modules.execution_engine import Side

    cash        = account_service.cash
    total_value = result.final_equity
    positions   = account_service._positions
    metrics     = result.metrics

    print("=" * 55)
    print(f"  策略: DualMATrendStrategy   标的: {SYMBOL}")
    print(f"  周期: {START_DATE.date()} ~ {END_DATE.date()}")
    print("-" * 55)
    print(f"  初始资金:   {result.initial_capital:>14,.2f}")
    print(f"  剩余现金:   {cash:>14,.2f}")

    for sym, pos in positions.items():
        if pos.quantity > 0:
            mv = pos.quantity * pos.average_cost
            total_value_display = mv
            print(f"  持仓 {sym}: {pos.quantity} 股 @ 均价 {pos.average_cost:.2f}  市值 ≈ {mv:,.2f}")

    pnl = total_value - result.initial_capital
    ret = pnl / result.initial_capital * 100
    print("-" * 55)
    print(f"  总资产估值: {total_value:>14,.2f}")
    print(f"  盈亏:       {pnl:>+14,.2f}  ({ret:+.2f}%)")
    print("-" * 55)
    print(f"  总收益率:   {metrics.get('total_return', 0):>13.2%}")
    print(f"  最大回撤:   {metrics.get('max_drawdown', 0):>13.2%}")
    print(f"  夏普比率:   {metrics.get('sharpe_ratio', 0):>13.2f}")
    print(f"  胜率:       {metrics.get('win_rate', 0):>13.2%}")
    print(f"  交易次数:   {len(result.trades):>13}")
    print("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="因子回测 + 可视化")
    parser.add_argument("--no-report", action="store_true", help="跳过生成可视化报告")
    parser.add_argument("--png",       action="store_true", help="生成 PNG 格式（默认 HTML）")
    args = parser.parse_args()

    run(
        save_report=not args.no_report,
        report_fmt="png" if args.png else "html",
    )
