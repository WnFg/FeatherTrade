from typing import Any, Dict, Optional, Type
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.strategy_manager import StrategyManager
from src.trading_system.modules.backtest_simulator import BacktestSimulator
from src.trading_system.modules.csv_data_feed import CSVDataFeed
from src.trading_system.modules.account_service import AccountService
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.risk.risk_manager import RiskManager
from src.trading_system.risk.fixed_stop_loss import FixedStopLossStrategy
from src.trading_system.risk.fixed_take_profit import FixedTakeProfitStrategy
from src.trading_system.backtest.recorder import BacktestRecorder
from src.trading_system.backtest.result import BacktestResult

class BacktestRunner:
    """
    Utility class to orchestrate a backtest session.
    """
    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        symbol: str,
        csv_path: str,
        strategy_params: Dict[str, Any] = None,
        initial_capital: float = 100000.0,
        enable_risk_management: bool = True
    ):
        self.engine = EventEngine()
        self.account_service = AccountService(self.engine, initial_cash=initial_capital)
        self.simulator = BacktestSimulator(self.engine, self.account_service)
        self.manager = StrategyManager(
            self.engine, 
            self.simulator, 
            account_service=self.account_service
        )
        
        if enable_risk_management:
            self.risk_manager = RiskManager(self.engine, self.account_service)
            # Default to 5% stop loss and 10% take profit for demonstration
            self.risk_manager.add_strategy(FixedStopLossStrategy({"stop_loss_pct": 0.05}))
            self.risk_manager.add_strategy(FixedTakeProfitStrategy({"take_profit_pct": 0.10}))
        else:
            self.risk_manager = None
        
        self.data_feed = CSVDataFeed(self.engine, symbol, csv_path)
        
        # Instantiate and add strategy
        self.strategy = strategy_class(self.engine, strategy_params)
        self.manager.add_strategy(self.strategy)
        
        self.initial_capital = initial_capital

        # Recorder for capturing backtest data (non-invasive)
        self.recorder = BacktestRecorder(
            self.engine, self.account_service, symbol, initial_capital
        )

    def run(self):
        """Starts the components and runs the backtest."""
        print("--- Starting Backtest ---")
        self.engine.start()
        self.data_feed.start()

        # Wait for the CSV feed to finish publishing all bars
        while self.data_feed._thread and self.data_feed._thread.is_alive():
            import time
            time.sleep(0.1)

        self.data_feed.stop()
        # engine.stop() calls queue.join() internally — waits for all events
        # (including FillEvents triggered by the last bars) to be processed.
        self.engine.stop()
        # Fill any orders submitted on the final bar that had no subsequent
        # MarketEvent to trigger _check_fills.
        self.simulator.flush_pending_orders()
        print("--- Backtest Complete ---")

    def get_results(
        self,
        verbose: bool = True,
        save_report: bool = False,
        report_path: str = "backtest_report.html",
    ) -> BacktestResult:
        """Retrieves structured backtest results from the recorder.

        Args:
            verbose: If True (default), print final cash and positions to console.
            save_report: If True, generate a visualisation report file.
            report_path: Output path for the report (HTML or PNG).

        Returns:
            A BacktestResult dataclass with full trade history, equity curve, and metrics.
        """
        result = self.recorder.build_result()

        if verbose:
            print("Final Account State:")
            print(f"  Cash: {self.account_service.cash:.2f}")
            print("  Positions:")
            for symbol, pos in self.account_service._positions.items():
                print(f"    {symbol}: {pos.quantity} units @ Avg Cost {pos.average_cost:.2f}")
            print(f"  Final Equity: {result.final_equity:.2f}")
            print(f"  Total Return: {result.metrics.get('total_return', 0):.2%}")
            print(f"  Max Drawdown: {result.metrics.get('max_drawdown', 0):.2%}")
            print(f"  Sharpe Ratio: {result.metrics.get('sharpe_ratio', 0):.2f}")
            print(f"  Win Rate:     {result.metrics.get('win_rate', 0):.2%}")

        if save_report:
            from src.trading_system.backtest.visualizer import BacktestVisualizer
            visualizer = BacktestVisualizer()
            visualizer.plot(result, output_path=report_path)
            print(f"  Report saved to: {report_path}")

        return result
