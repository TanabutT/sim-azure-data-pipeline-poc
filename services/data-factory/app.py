import logging
import asyncio
import json
import os
import sys
import time
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.common import Config
from services.data_factory.database import DatabaseManager
from services.data_factory.orchestrator import PipelineOrchestrator
from services.data_factory.scheduler import PipelineScheduler
from .models import (
    Pipeline,
    PipelineRun,
    PipelineRunRequest,
    PipelineRunStatus,
    RunTrigger
)

logging.basicConfig(
    level=Config.log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

db_manager = None
orchestrator = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global db_manager, orchestrator, scheduler

    logger.info("Starting Data Factory service...")

    db_manager = DatabaseManager(Config.database_url())
    orchestrator = PipelineOrchestrator(db_manager)
    scheduler = PipelineScheduler()
    scheduler.start()

    logger.info("Data Factory service started")

    yield

    scheduler.stop()
    logger.info("Data Factory service stopped")


app = FastAPI(
    title="Azure Data Factory POC",
    description="Simulated Azure Data Factory service",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-factory"}


@app.get("/api/pipelines")
async def list_pipelines():
    """List all pipelines"""
    try:
        pipelines = db_manager.list_pipelines()
        return {
            "status": "success",
            "count": len(pipelines),
            "pipelines": [
                {
                    "id": p.id,
                    "name": p.name,
                    "created_at": p.created_at.isoformat(),
                    "activities_count": len(p.definition.get('activities', []))
                }
                for p in pipelines
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipelines/{pipeline_name}")
async def get_pipeline(pipeline_name: str):
    """Get a specific pipeline"""
    try:
        pipeline = db_manager.get_pipeline_by_name(pipeline_name)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")

        return {
            "status": "success",
            "pipeline": {
                "id": pipeline.id,
                "name": pipeline.name,
                "definition": pipeline.definition,
                "created_at": pipeline.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipelines")
async def create_pipeline(pipeline: Pipeline):
    """Create a new pipeline"""
    try:
        existing = db_manager.get_pipeline_by_name(pipeline.name)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Pipeline '{pipeline.name}' already exists"
            )

        definition = {
            "name": pipeline.name,
            "description": pipeline.description,
            "activities": [a.dict() for a in pipeline.activities],
            "triggers": pipeline.triggers or [],
            "parameters": pipeline.parameters or {},
            "variables": pipeline.variables or {}
        }

        db_pipeline = db_manager.create_pipeline(pipeline.name, definition)

        return {
            "status": "success",
            "pipeline": {
                "id": db_pipeline.id,
                "name": db_pipeline.name,
                "created_at": db_pipeline.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipelines/{pipeline_name}/run")
async def run_pipeline(
    pipeline_name: str,
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks
):
    """Trigger a pipeline execution"""
    try:
        pipeline = db_manager.get_pipeline_by_name(pipeline_name)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")

        async def execute_in_background():
            await orchestrator.execute_pipeline(
                pipeline.id,
                pipeline.name,
                pipeline.definition,
                request.parameters
            )

        background_tasks.add_task(execute_in_background)

        run = db_manager.create_run(pipeline.id, pipeline_name)

        return {
            "status": "success",
            "run_id": run.id,
            "pipeline_name": pipeline_name,
            "trigger": request.trigger,
            "message": "Pipeline execution started"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs")
async def list_runs(pipeline_id: Optional[int] = None, limit: int = 100):
    """List pipeline runs"""
    try:
        runs = db_manager.list_runs(pipeline_id, limit)
        return {
            "status": "success",
            "count": len(runs),
            "runs": [
                {
                    "id": r.id,
                    "pipeline_name": r.pipeline_name,
                    "status": r.status,
                    "start_time": r.start_time.isoformat() if r.start_time else None,
                    "end_time": r.end_time.isoformat() if r.end_time else None,
                    "created_at": r.created_at.isoformat()
                }
                for r in runs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}")
async def get_run(run_id: int):
    """Get a specific pipeline run"""
    try:
        run = db_manager.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        activities = orchestrator.get_run_activities(run_id)

        return {
            "status": "success",
            "run": {
                "id": run.id,
                "pipeline_name": run.pipeline_name,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "error_message": run.error_message,
                "activities": activities,
                "created_at": run.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health/database")
async def database_health():
    """Check database connectivity"""
    try:
        pipelines = db_manager.list_pipelines()
        return {
            "status": "healthy",
            "component": "database",
            "pipelines_count": len(pipelines)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database is not accessible"
        )


@app.get("/api/scheduled-jobs")
async def list_scheduled_jobs():
    """List all scheduled jobs"""
    try:
        jobs = scheduler.list_scheduled_jobs()
        return {
            "status": "success",
            "count": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Failed to list scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.api_host(),
        port=Config.api_port()
    )
