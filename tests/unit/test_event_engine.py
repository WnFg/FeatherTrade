import unittest
import time
from src.trading_system.core.event_engine import EventEngine
from src.trading_system.core.event_types import Event

class TestEventEngine(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()
        self.engine.start()

    def tearDown(self):
        self.engine.stop()

    def test_event_propagation(self):
        """Test if a registered handler receives the event."""
        received_data = []

        def handler(event):
            received_data.append(event.data)

        self.engine.register("test_event", handler)
        
        test_event = Event("test_event", "hello")
        self.engine.put(test_event)
        
        # Give some time for background processing
        time.sleep(0.5)
        
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], "hello")

    def test_unregister_handler(self):
        """Test if an unregistered handler no longer receives events."""
        received_data = []

        def handler(event):
            received_data.append(event.data)

        self.engine.register("test_event", handler)
        self.engine.unregister("test_event", handler)
        
        test_event = Event("test_event", "hello")
        self.engine.put(test_event)
        
        time.sleep(0.5)
        
        self.assertEqual(len(received_data), 0)

if __name__ == '__main__':
    unittest.main()
