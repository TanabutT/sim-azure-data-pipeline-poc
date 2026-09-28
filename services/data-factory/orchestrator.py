import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from .database import DatabaseManager, RunModel, ActivityExecutionModel
from .models import PipelineRunStatus, Pipeline, Activity, ActivityType
from .activities import create_activity

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates pipeline execution"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def execute_pipeline(
        self,
        pipeline_id: int,
        pipeline_name: str,
        definition: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> RunModel:
        """Execute a pipeline and track its progress"""

        run = self.db.create_run(pipeline_id, pipeline_name, PipelineRunStatus.RUNNING.value)
        self.db.update_run_status(run.id, PipelineRunStatus.RUNNING.value)

        logger.info(f"Starting execution of pipeline '{pipeline_name}' (Run ID: {run.id})")

        try:
            activities = definition.get('activities', [])
            activity_executions = []

            for activity_config in activities:
                activity_execution = await self._execute_activity(
                    run.id,
                    activity_config,
                    parameters
                )
                activity_executions.append(activity_execution)

                if activity_execution['status'] == PipelineRunStatus.FAILED.value:
                    self.db.update_run_status(
                        run.id,
                        PipelineRunStatus.FAILED.value,
                        f"Activity '{activity_config['name']}' failed"
                    )
                    logger.error(f"Pipeline run {run.id} failed at activity '{activity_config['name']}'")
                    return self.db.get_run(run.id)

            self.db.update_run_status(run.id, PipelineRunStatus.SUCCEEDED.value)
            logger.info(f"Pipeline run {run.id} completed successfully")

        except Exception as e:
            self.db.update_run_status(
                run.id,
                PipelineRunStatus.FAILED.value,
                str(e)
            )
            logger.error(f"Pipeline run {run.id} failed with error: {e}")

        return self.db.get_run(run.id)

    async def _execute_activity(
        self,
        run_id: int,
        activity_config: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single activity"""

        activity_name = activity_config.get('name')
        activity_type = activity_config.get('type')
        config = activity_config.get('config', {})

        logger.info(f"Executing activity '{activity_name}' (Type: {activity_type})")

        execution_record = self.db.create_activity_execution(
            run_id,
            activity_name,
            activity_type
        )

        try:
            self.db.update_activity_execution(
                execution_record.id,
                PipelineRunStatus.RUNNING.value
            )

            activity = create_activity(activity_name, activity_type, config)

            output = await activity.execute()

            self.db.update_activity_execution(
                execution_record.id,
                PipelineRunStatus.SUCCEEDED.value,
                output
            )

            logger.info(f"Activity '{activity_name}' completed successfully")

            return {
                'name': activity_name,
                'type': activity_type,
                'status': PipelineRunStatus.SUCCEEDED.value,
                'output': output
            }

        except Exception as e:
            error_msg = str(e)
            self.db.update_activity_execution(
                execution_record.id,
                PipelineRunStatus.FAILED.value,
                error_message=error_msg
            )

            logger.error(f"Activity '{activity_name}' failed: {error_msg}")

            return {
                'name': activity_name,
                'type': activity_type,
                'status': PipelineRunStatus.FAILED.value,
                'error': error_msg
            }

    def get_run_status(self, run_id: int) -> Optional[RunModel]:
        """Get the status of a pipeline run"""
        return self.db.get_run(run_id)

    def get_run_activities(self, run_id: int) -> List[Dict[str, Any]]:
        """Get all activity executions for a run"""
        executions = self.db.get_activity_executions(run_id)
        return [
            {
                'id': e.id,
                'name': e.activity_name,
                'type': e.activity_type,
                'status': e.status,
                'start_time': e.start_time,
                'end_time': e.end_time,
                'output': e.output,
                'error': e.error_message
            }
            for e in executions
        ]
