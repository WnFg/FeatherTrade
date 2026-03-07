import queue
import threading
from typing import Callable, Dict, List, Any
from src.trading_system.core.event_types import Event

class EventEngine:
    """
    Event-driven engine that manages an event queue and dispatches events 
    to registered callback handlers.
    """
    def __init__(self):
        self._queue = queue.Queue()
        self._handlers: Dict[str, List[Callable]] = {}
        self._active = False
        self._thread = threading.Thread(target=self._run)

    def start(self):
        """Start the event engine thread."""
        self._active = True
        self._thread.start()

    def stop(self):
        """Stop the event engine thread."""
        self._active = False
        self._queue.put(None)  # Sentinel to unblock the queue
        self._thread.join()

    def put(self, event: Event):
        """Put an event into the queue."""
        self._queue.put(event)

    def register(self, event_type: str, handler: Callable):
        """Register a handler function for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unregister(self, event_type: str, handler: Callable):
        """Unregister a handler function for a specific event type."""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

    def _run(self):
        """The main execution loop in the background thread."""
        while self._active:
            try:
                event = self._queue.get(timeout=1.0)
                if event is None:
                    break
                
                self._dispatch(event)
            except queue.Empty:
                continue

    def _dispatch(self, event: Event):
        """Dispatch an event to all registered handlers."""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in handler for event {event.type}: {e}")
