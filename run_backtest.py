from src.trading_system.core.backtest_runner import BacktestRunner
from src.trading_system.strategies.moving_average_crossover import MovingAverageCrossover

def main():
    runner = BacktestRunner(
        strategy_class=MovingAverageCrossover,
        symbol="AAPL",
        csv_path="sample_data.csv",
        strategy_params={"fast_period": 5, "slow_period": 15, "quantity": 100}
    )

    runner.run()
    result = runner.get_results(save_report=True, report_path="backtest_report.html")
    print(f"\n[回测完成] 报告已生成: backtest_report.html")
    print(f"[回测完成] 共 {len(result.trades)} 笔成交，净值终值: {result.final_equity:.2f}")

if __name__ == '__main__':
    main()
