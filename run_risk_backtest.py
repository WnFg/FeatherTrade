from src.trading_system.core.backtest_runner import BacktestRunner
from src.trading_system.strategies.moving_average_crossover import MovingAverageCrossover

def main():
    runner = BacktestRunner(
        strategy_class=MovingAverageCrossover,
        symbol="AAPL",
        csv_path="risk_sample_data.csv",
        strategy_params={"fast_period": 2, "slow_period": 5, "quantity": 100},
        initial_capital=100000.0,
        enable_risk_management=True
    )
    
    runner.run()
    runner.get_results()

if __name__ == '__main__':
    main()
