import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from .models import ScheduledTask, TaskExecutionLog
from .service import FactorService
from .config import ScheduleConfig
from .time_resolver import TimeRangeResolver

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Manages scheduling and execution of factor computation tasks."""

    def __init__(self, factor_service: FactorService, jobstores: Optional[Dict[str, Any]] = None):
        self.factor_service = factor_service
        self.db = factor_service.db

        if jobstores is None:
            jobstores = {
                'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
            }
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.scheduler.start()

    def add_task(self, task: ScheduledTask):
        """Adds a task to the scheduler based on its trigger configuration."""
        if not task.is_active:
            return

        trigger = self._create_trigger(task.trigger_type, task.trigger_config)

        # We wrap the execution to handle logging and status
        self.scheduler.add_job(
            func=self._execute_task_wrapper,
            trigger=trigger,
            args=[task.id],
            id=f"task_{task.id}",
            replace_existing=True,
            coalesce=True,
            max_instances=1
        )
        logger.info(f"Scheduled task {task.id} with trigger {task.trigger_type}")

    def add_task_from_config(self, config: ScheduleConfig):
        """Adds a task from a ScheduleConfig (config-driven scheduling)."""
        trigger_type = config.trigger.get('type', 'cron')

        # Extract trigger config based on type
        if trigger_type == 'cron':
            trigger_config = config.trigger.get('expr')
        elif trigger_type == 'interval':
            # For interval, pass the dict without 'type' key
            trigger_config = {k: v for k, v in config.trigger.items() if k != 'type'}
        elif trigger_type == 'one-off':
            trigger_config = config.trigger.get('run_time')
        else:
            trigger_config = config.trigger

        trigger = self._create_trigger(trigger_type, trigger_config)

        # Use config name as job ID
        self.scheduler.add_job(
            func=self._execute_config_task_wrapper,
            trigger=trigger,
            args=[config.name],
            id=f"config_task_{config.name}",
            replace_existing=True,
            coalesce=True,
            max_instances=1
        )
        logger.info(f"Scheduled config task {config.name} with trigger {trigger_type}")

    def remove_task(self, task_id: int):
        """Removes a task from the scheduler."""
        job_id = f"task_{task_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed task {task_id} from scheduler")

    def trigger_now(self, task_id: int):
        """Manually triggers a task execution immediately."""
        self.scheduler.add_job(
            func=self._execute_task_wrapper,
            trigger=DateTrigger(run_date=datetime.now()),
            args=[task_id],
            id=f"manual_task_{task_id}_{datetime.now().timestamp()}"
        )

    def _create_trigger(self, trigger_type: str, config: Any):
        """Creates an APScheduler trigger from config."""
        if trigger_type == 'cron':
            # config can be a cron string or a dict of fields
            if isinstance(config, str):
                return CronTrigger.from_crontab(config)
            return CronTrigger(**config)
        elif trigger_type == 'interval':
            return IntervalTrigger(**config)
        elif trigger_type == 'one-off':
            run_date = datetime.fromisoformat(config) if isinstance(config, str) else config
            return DateTrigger(run_date=run_date)
        else:
            raise ValueError(f"Unsupported trigger type: {trigger_type}")

    def _execute_task_wrapper(self, task_id: int):
        """Wrapper to execute task and log results (DB-driven tasks)."""
        task = self.db.get_scheduled_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found in database during execution")
            return

        # 1. Create execution log
        log_id = self.db.insert_execution_log(TaskExecutionLog(
            id=None,
            task_id=task_id,
            start_time=datetime.now(),
            status='RUNNING'
        ))

        try:
            # 2. Get data source instance and factor definition
            ds_instance = self.db.get_data_source_instance(task.data_source_instance_id)
            if not ds_instance:
                raise ValueError(f"DataSourceInstance {task.data_source_instance_id} not found")

            factor_def = self.db.get_factor_definition_by_id(task.factor_definition_id)
            if not factor_def:
                raise ValueError(f"FactorDefinition {task.factor_definition_id} not found")

            # 3. Resolve symbols — support both single 'symbol' and list 'symbols'
            symbols = ds_instance.parameters.get('symbols', [])
            single_symbol = ds_instance.parameters.get('symbol')
            if not symbols and single_symbol:
                symbols = [single_symbol]
            if not symbols:
                symbols = ['UNKNOWN']

            # 4. Resolve time range from parameters or use default
            time_range = ds_instance.parameters.get('time_range', {})
            if time_range:
                start_time = TimeRangeResolver.resolve(time_range.get('start', 'today'))
                end_time = TimeRangeResolver.resolve(time_range.get('end', 'today'))
            else:
                # Default: today
                start_time = TimeRangeResolver.resolve('today')
                end_time = TimeRangeResolver.resolve('today')

            # 5. Execute for each symbol
            for symbol in symbols:
                self.factor_service.compute_and_store(
                    symbol=symbol,
                    factor_name=factor_def.name,
                    source_name_or_id=task.data_source_instance_id,
                    start_time=start_time,
                    end_time=end_time
                )

            # 6. Update log to SUCCESS
            self.db.update_execution_log(log_id, datetime.now(), 'SUCCESS')
            logger.info(f"Task {task_id} executed successfully for {len(symbols)} symbol(s)")

        except Exception as e:
            # 7. Update log to FAILURE
            self.db.update_execution_log(log_id, datetime.now(), 'FAILURE', str(e))
            logger.error(f"Task {task_id} failed: {e}")

    def _execute_config_task_wrapper(self, config_name: str):
        """Wrapper to execute config-driven task with logging."""
        start_time = datetime.now()

        # Get ScheduleConfig from registry
        schedule_config = self.factor_service.registry.get_schedule_config(config_name)
        if not schedule_config:
            logger.error(f"ScheduleConfig {config_name} not found")
            return

        # Get associated DataSourceConfig
        ds_config = self.factor_service.registry.get_data_source_config(schedule_config.data_source)
        if not ds_config:
            logger.error(f"DataSourceConfig {schedule_config.data_source} not found")
            return

        success_count = 0
        failure_count = 0
        error_messages = []

        try:
            # Extract symbols from DataSourceConfig
            symbols = ds_config.params.get('symbols', [])
            if not symbols:
                logger.warning(f"No symbols found in DataSourceConfig {ds_config.name}")
                return

            # Resolve time range from DataSourceConfig
            if ds_config.time_range:
                start_time_data = TimeRangeResolver.resolve(ds_config.time_range.get('start', 'today'))
                end_time_data = TimeRangeResolver.resolve(ds_config.time_range.get('end', 'today'))
            else:
                # Default: today
                start_time_data = TimeRangeResolver.resolve('today')
                end_time_data = TimeRangeResolver.resolve('today')

            # Execute for each symbol
            for symbol in symbols:
                try:
                    self.factor_service.compute_and_store(
                        symbol=symbol,
                        factor_name=schedule_config.factor,
                        source_name_or_id=schedule_config.data_source,
                        start_time=start_time_data,
                        end_time=end_time_data
                    )
                    success_count += 1
                    logger.info(f"Config task {config_name} executed successfully for {symbol}")
                except Exception as e:
                    failure_count += 1
                    error_msg = f"{symbol}: {str(e)}"
                    error_messages.append(error_msg)
                    logger.error(f"Config task {config_name} failed for {symbol}: {e}")

            # Log summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            status = 'SUCCESS' if failure_count == 0 else ('PARTIAL' if success_count > 0 else 'FAILURE')

            logger.info(
                f"Config task {config_name} completed: {success_count} succeeded, {failure_count} failed, "
                f"duration: {duration:.2f}s, status: {status}"
            )

        except Exception as e:
            logger.error(f"Config task {config_name} failed: {e}")

    def load_all_tasks(self):
        """Loads all active tasks from DB into scheduler."""
        tasks = self.db.get_all_active_tasks()
        for task in tasks:
            self.add_task(task)

    def load_all_config_tasks(self):
        """Loads all ScheduleConfig tasks from registry into scheduler."""
        # Access schedule configs from registry
        for config_name, config in self.factor_service.registry._schedule_config_map.items():
            if config.is_active:
                self.add_task_from_config(config)
