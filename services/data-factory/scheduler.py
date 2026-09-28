import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Manages pipeline scheduling and triggers"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Pipeline scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Pipeline scheduler stopped")

    def add_scheduled_trigger(
        self,
        pipeline_name: str,
        trigger_config: Dict[str, Any],
        callback: Callable
    ):
        """Add a scheduled trigger for a pipeline"""

        trigger_type = trigger_config.get('type', 'Scheduled')
        recurrence = trigger_config.get('recurrence', {})

        try:
            if trigger_type == 'Scheduled':
                frequency = recurrence.get('frequency', 'Daily')
                interval = recurrence.get('interval', 1)
                start_time = recurrence.get('startTime')

                if frequency == 'Daily':
                    trigger = CronTrigger(
                        hour=0,
                        minute=0,
                        timezone='UTC'
                    )
                elif frequency == 'Weekly':
                    day_of_week = recurrence.get('dayOfWeek', 'mon')
                    trigger = CronTrigger(
                        day_of_week=day_of_week,
                        hour=0,
                        minute=0,
                        timezone='UTC'
                    )
                elif frequency == 'Hourly':
                    trigger = CronTrigger(
                        minute=0,
                        timezone='UTC'
                    )
                else:
                    logger.warning(f"Unsupported frequency: {frequency}")
                    return

                job_id = f"scheduled_{pipeline_name}_{datetime.utcnow().timestamp()}"
                job = self.scheduler.add_job(
                    callback,
                    trigger=trigger,
                    id=job_id,
                    args=[pipeline_name],
                    replace_existing=True
                )

                self.jobs[job_id] = {
                    'pipeline': pipeline_name,
                    'trigger_type': trigger_type,
                    'frequency': frequency,
                    'next_run': job.next_run_time
                }

                logger.info(
                    f"Scheduled pipeline '{pipeline_name}' with frequency '{frequency}'"
                )

        except Exception as e:
            logger.error(f"Failed to add scheduled trigger for '{pipeline_name}': {e}")

    def add_event_trigger(
        self,
        pipeline_name: str,
        trigger_config: Dict[str, Any],
        callback: Callable
    ):
        """Add an event-based trigger for a pipeline"""

        event_type = trigger_config.get('event_type')
        properties = trigger_config.get('properties', {})

        logger.info(
            f"Registered event trigger for pipeline '{pipeline_name}' (Event: {event_type})"
        )

    def trigger_pipeline_immediately(
        self,
        pipeline_name: str,
        callback: Callable,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Trigger a pipeline execution immediately"""

        try:
            job_id = f"manual_{pipeline_name}_{datetime.utcnow().timestamp()}"

            if parameters:
                self.scheduler.add_job(
                    callback,
                    id=job_id,
                    args=[pipeline_name, parameters]
                )
            else:
                self.scheduler.add_job(
                    callback,
                    id=job_id,
                    args=[pipeline_name]
                )

            logger.info(f"Triggered pipeline '{pipeline_name}' immediately")

        except Exception as e:
            logger.error(f"Failed to trigger pipeline '{pipeline_name}': {e}")

    def list_scheduled_jobs(self) -> Dict[str, Any]:
        """List all scheduled jobs"""

        jobs_info = {}

        for job in self.scheduler.get_jobs():
            jobs_info[job.id] = {
                'pipeline': job.args[0] if job.args else None,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }

        return jobs_info

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""

        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed scheduled job '{job_id}'")
        except Exception as e:
            logger.error(f"Failed to remove job '{job_id}': {e}")

    def get_next_run_times(self, pipeline_name: str, count: int = 10) -> list:
        """Get next run times for a pipeline"""

        next_runs = []

        for job in self.scheduler.get_jobs():
            if job.args and job.args[0] == pipeline_name:
                next_run = job.next_run_time
                for i in range(count):
                    if next_run:
                        next_runs.append(next_run)
                        next_run = next_run + timedelta(days=1)

        return next_runs[:count]
