import csv
import threading
import time
from datetime import datetime
from src.trading_system.modules.signal_module import AbstractSignalSource
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import MarketEvent
from src.trading_system.data.market_data import Bar

class CSVDataFeed(AbstractSignalSource):
    """
    Reads historical bar data from a CSV file and feeds it into the EventEngine.
    Expects CSV header: timestamp,open,high,low,close,volume
    """
    def __init__(self, event_engine: EventEngine, symbol: str, file_path: str):
        super().__init__(event_engine)
        self._symbol = symbol
        self._file_path = file_path
        self._active = False
        self._thread = None

    def start(self):
        """Starts a background thread to read the CSV file."""
        self._active = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self):
        """Stops the CSV reading thread."""
        self._active = False
        if self._thread:
            self._thread.join()

    def _run(self):
        """Reads the CSV file line by line and puts events into the engine."""
        try:
            with open(self._file_path, mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not self._active:
                        break
                    
                    try:
                        # 2.3 Basic Data Validation
                        bar = self._parse_and_validate(row)
                        if bar:
                            event = MarketEvent(bar)
                            self._event_engine.put(event)
                            time.sleep(0.01)  # Small delay to allow processing
                    except Exception as e:
                        print(f"Error parsing row {row}: {e}")
                        
        except FileNotFoundError:
            print(f"CSV file not found: {self._file_path}")

    def _parse_and_validate(self, row: dict) -> Bar:
        """Parses a CSV row into a Bar object with validation."""
        try:
            # Expected format: 2023-01-01 09:30:00
            timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # Numeric validation
            open_p = float(row['open'])
            high = float(row['high'])
            low = float(row['low'])
            close = float(row['close'])
            volume = int(row['volume'])
            
            if any(p <= 0 for p in [open_p, high, low, close]):
                print(f"Warning: Invalid non-positive price in row: {row}")
                return None
            
            if high < max(open_p, low, close) or low > min(open_p, high, close):
                 print(f"Warning: Inconsistent High/Low prices in row: {row}")
                 return None

            return Bar(
                symbol=self._symbol,
                timestamp=timestamp,
                open=open_p,
                high=high,
                low=low,
                close=close,
                volume=volume
            )
        except (ValueError, KeyError) as e:
            print(f"Validation error: {e}")
            return None
