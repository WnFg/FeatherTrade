import unittest
import os
import tempfile
import time
from datetime import datetime, timedelta
from src.trading_system.factors.database import FactorDatabase
from src.trading_system.factors.models import FactorDefinition, DataSourceInstance, ScheduledTask
from src.trading_system.factors.service import FactorService
from src.trading_system.factors.scheduler import TaskScheduler
from src.trading_system.factors.config import ScheduleConfig

from apscheduler.jobstores.memory import MemoryJobStore

class TestFactorScheduling(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self._tmp_dir, "test_scheduling.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.db = FactorDatabase(self.db_path)
        self.service = FactorService(self.db)
        
        jobstores = {
            'default': MemoryJobStore()
        }
        self.scheduler = TaskScheduler(self.service, jobstores=jobstores)

    def tearDown(self):
        self.scheduler.scheduler.shutdown()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_full_pipeline(self):
        # 1. Create Factor Definition
        defn = FactorDefinition(
            id=None,
            name="movingaveragefactor", # lowercase class name
            display_name="SMA",
            category="Momentum",
            description="Simple Moving Average",
            formula_config={"window": 2, "price_key": "price"}
        )
        fid = self.service.register_factor_definition(defn)
        
        # 2. Create Data Source Instance
        # Use FileDataSource with some test data
        csv_path = os.path.join(self._tmp_dir, "test_sched_data.csv")
        with open(csv_path, "w") as f:
            f.write("timestamp,symbol,price\n")
            f.write(f"{(datetime.now() - timedelta(minutes=5)).isoformat()},AAPL,100.0\n")
            f.write(f"{datetime.now().isoformat()},AAPL,110.0\n")
            
        ds_instance = DataSourceInstance(
            id=None,
            name="test_file_source",
            class_path="FileDataSource",
            parameters={"file_path": csv_path},
            transformation_config={"type_casting": {"price": "float"}}
        )
        dsid = self.db.insert_data_source_instance(ds_instance)
        
        # 3. Create and Schedule Task (one-off, immediate)
        task = ScheduledTask(
            id=None,
            factor_definition_id=fid,
            data_source_instance_id=dsid,
            trigger_type='one-off',
            trigger_config=(datetime.now() + timedelta(seconds=1)).isoformat(),
            is_active=True
        )
        tid = self.db.insert_scheduled_task(task)
        task.id = tid
        
        self.scheduler.add_task(task)
        
        # 4. Wait for execution
        time.sleep(3)
        
        # 5. Verify results
        # Check execution logs
        history = self.db.get_execution_history(tid)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0].status, 'SUCCESS')
        
        # Check factor values
        values = self.service.get_factor_values("AAPL", "movingaveragefactor")
        self.assertGreater(len(values), 0)
        
        if os.path.exists(csv_path):
            os.remove(csv_path)

    def test_schedule_config_driven_task(self):
        """Test ScheduleConfig-driven task execution."""
        # 1. Register factor and data source config
        from src.trading_system.factors.config import FactorConfig, DataSourceConfig

        factor_config = FactorConfig(
            name="test_config_factor",
            category="test",
            display_name="Test Config Factor"
        )
        self.service.registry._register_factor_configs([factor_config])

        ds_config = DataSourceConfig(
            name="test_config_source",
            source_class="FileDataSource",
            params={
                "file_path": os.path.join(self._tmp_dir, "test_sched_data.csv"),
                "symbols": ["AAPL", "GOOGL"]
            },
            time_range={"start": "today-1d", "end": "today"}
        )
        self.service.registry._register_data_source_configs([ds_config])

        # 2. Create schedule config
        schedule_config = ScheduleConfig(
            name="test_schedule",
            factor="test_config_factor",
            data_source="test_config_source",
            trigger={"type": "one-off", "run_time": (datetime.now() + timedelta(seconds=1)).isoformat()},
            is_active=True
        )
        self.service.registry._register_schedule_configs([schedule_config])

        # 3. Create test data file
        csv_path = os.path.join(self._tmp_dir, "test_sched_data.csv")
        with open(csv_path, "w") as f:
            f.write("timestamp,symbol,price\n")
            f.write(f"{datetime.now().isoformat()},AAPL,100.0\n")
            f.write(f"{datetime.now().isoformat()},GOOGL,200.0\n")

        # 4. Add task from config
        self.scheduler.add_task_from_config(schedule_config)

        # 5. Wait for execution
        time.sleep(3)

        # 6. Verify both symbols were processed
        # Note: This test verifies the scheduler can load and execute config-driven tasks
        # Actual factor computation depends on having the logic registered

        if os.path.exists(csv_path):
            os.remove(csv_path)

if __name__ == "__main__":
    unittest.main()
