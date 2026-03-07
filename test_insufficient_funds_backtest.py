from src.trading_system.core.backtest_runner import BacktestRunner
from src.trading_system.strategies.moving_average_crossover import MovingAverageCrossover

def main():
    # Run backtest with very low initial capital ($100)
    # The SMA strategy tries to buy 100 units of AAPL (approx $10000)
    # This should trigger REJECTED orders in the simulator
    runner = BacktestRunner(
        strategy_class=MovingAverageCrossover,
        symbol="AAPL",
        csv_path="sample_data.csv",
        strategy_params={"fast_period": 5, "slow_period": 15, "quantity": 100},
        initial_capital=100.0 
    )
    
    runner.run()
    runner.get_results()

if __name__ == '__main__':
    main()
