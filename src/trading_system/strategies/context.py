from typing import Any, Dict, Optional

class StrategyContext:
    """
    Unified interface for strategies to access external services and 
    maintain session-level state.
    """
    def __init__(self, 
                 strategy_id: str,
                 account_service: Any, 
                 execution_engine: Any, 
                 factor_service: Optional[Any] = None):
        self.strategy_id = strategy_id
        self.account = account_service
        self.execution = execution_engine
        self.factors = factor_service
        self._state: Dict[str, Any] = {}

    @property
    def state(self):
        """Access to the local memory KV store."""
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the KV store."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        """Store a value in the KV store."""
        self._state[key] = value

    def clear(self):
        """Clear the KV store."""
        self._state.clear()
