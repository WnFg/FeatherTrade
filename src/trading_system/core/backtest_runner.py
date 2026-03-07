import time
from typing import Any, Dict, Type
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.strategy_manager import StrategyManager
from src.trading_system.modules.backtest_simulator import BacktestSimulator
from src.trading_system.modules.csv_data_feed import CSVDataFeed
from src.trading_system.modules.account_service import AccountService
from src.trading_system.strategies.base_strategy import BaseStrategy
from src.trading_system.risk.risk_manager import RiskManager
from src.trading_system.risk.fixed_stop_loss import FixedStopLossStrategy
from src.trading_system.risk.fixed_take_profit import FixedTakeProfitStrategy

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

    def run(self):
        """Starts the components and runs the backtest."""
        print("--- Starting Backtest ---")
        self.engine.start()
        self.data_feed.start()
        
        # Wait for data feed to finish
        while self.data_feed._thread and self.data_feed._thread.is_alive():
             time.sleep(1)
             
        # Allow time for remaining events to be processed
        time.sleep(2)
        
        self.data_feed.stop()
        self.engine.stop()
        print("--- Backtest Complete ---")

    def get_results(self):
        """Retrieves and displays backtest results from AccountService."""
        print("Final Account State:")
        print(f"  Cash: {self.account_service.cash:.2f}")
        print("  Positions:")
        for symbol, pos in self.account_service._positions.items():
            print(f"    {symbol}: {pos.quantity} units @ Avg Cost {pos.average_cost:.2f}")
