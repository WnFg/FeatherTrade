"""
FactorDataFeed: feeds Bar events from the factor database.

Drop-in replacement for CSVDataFeed when OHLCV data is stored as factors
(e.g. via TuShareDataSource / quick_register).

Usage:
    feed = FactorDataFeed(
        event_engine=engine,
        symbol="000001.SZ",
        factor_service=svc,
        open_factor="daily_open",
        high_factor="daily_high",
        low_factor="daily_low",
        close_factor="daily_close",
        volume_factor="daily_vol",   # optional
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2025, 1, 1),
    )
"""
import threading
import time
from datetime import datetime
from typing import Optional, Any

from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import MarketEvent
from src.trading_system.data.market_data import Bar
from src.trading_system.modules.signal_module import AbstractSignalSource


class FactorDataFeed(AbstractSignalSource):
    """
    Reads OHLCV bar data from the factor database and emits MarketEvents.

    Each bar is assembled by aligning factor values on their timestamp.
    Timestamps without a full set of OHLC values are skipped.
    """

    def __init__(
        self,
        event_engine: EventEngine,
        symbol: str,
        factor_service: Any,
        open_factor: str = "daily_open",
        high_factor: str = "daily_high",
        low_factor: str = "daily_low",
        close_factor: str = "daily_close",
        volume_factor: Optional[str] = "daily_vol",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        super().__init__(event_engine)
        self._symbol = symbol
        self._svc = factor_service
        self._open_factor = open_factor
        self._high_factor = high_factor
        self._low_factor = low_factor
        self._close_factor = close_factor
        self._volume_factor = volume_factor
        self._start_time = start_time
        self._end_time = end_time
        self._active = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False
        if self._thread:
            self._thread.join()

    def _run(self):
        bars = self._load_bars()
        for bar in bars:
            if not self._active:
                break
            self._event_engine.put(MarketEvent(bar))
            time.sleep(0.01)  # allow engine thread to process bar + downstream events
        self._active = False

    def _load_bars(self):
        """Assemble Bar objects by aligning OHLCV factor values on timestamp."""
        def _to_map(factor_name):
            values = self._svc.get_factor_values(
                self._symbol, factor_name,
                start_time=self._start_time,
                end_time=self._end_time,
            )
            # factor values are returned newest-first; reverse to chronological
            return {v.timestamp: v.value for v in reversed(values)}

        opens = _to_map(self._open_factor)
        highs = _to_map(self._high_factor)
        lows = _to_map(self._low_factor)
        closes = _to_map(self._close_factor)
        volumes = _to_map(self._volume_factor) if self._volume_factor else {}

        # Use close timestamps as the master timeline (always present)
        timestamps = sorted(closes.keys())

        bars = []
        for ts in timestamps:
            if ts not in opens or ts not in highs or ts not in lows:
                continue  # skip incomplete bars
            bars.append(Bar(
                symbol=self._symbol,
                timestamp=ts,
                open=opens[ts],
                high=highs[ts],
                low=lows[ts],
                close=closes[ts],
                volume=int(volumes.get(ts, 0)),
            ))
        return bars
