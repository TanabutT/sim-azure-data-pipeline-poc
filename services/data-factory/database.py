import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .models import PipelineRunStatus, ActivityType

logger = logging.getLogger(__name__)

Base = declarative_base()


class PipelineModel(Base):
    __tablename__ = 'pipelines'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    definition = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RunModel(Base):
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), nullable=False)
    pipeline_name = Column(String(255), nullable=False)
    status = Column(String(50), default=PipelineRunStatus.PENDING.value)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityExecutionModel(Base):
    __tablename__ = 'activity_executions'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('runs.id'), nullable=False)
    activity_name = Column(String(255), nullable=False)
    activity_type = Column(String(50), nullable=False)
    status = Column(String(50), default=PipelineRunStatus.PENDING.value)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    output = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Manage database operations"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._init_db()
        logger.info(f"Connected to database: {database_url}")

    def _init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables initialized")

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()

    def create_pipeline(self, name: str, definition: dict) -> PipelineModel:
        """Create a new pipeline"""
        session = self.get_session()
        try:
            pipeline = PipelineModel(name=name, definition=definition)
            session.add(pipeline)
            session.commit()
            session.refresh(pipeline)
            logger.info(f"Created pipeline: {name}")
            return pipeline
        finally:
            session.close()

    def get_pipeline(self, pipeline_id: int) -> Optional[PipelineModel]:
        """Get pipeline by ID"""
        session = self.get_session()
        try:
            return session.query(PipelineModel).filter(PipelineModel.id == pipeline_id).first()
        finally:
            session.close()

    def get_pipeline_by_name(self, name: str) -> Optional[PipelineModel]:
        """Get pipeline by name"""
        session = self.get_session()
        try:
            return session.query(PipelineModel).filter(PipelineModel.name == name).first()
        finally:
            session.close()

    def list_pipelines(self) -> List[PipelineModel]:
        """List all pipelines"""
        session = self.get_session()
        try:
            return session.query(PipelineModel).all()
        finally:
            session.close()

    def create_run(self, pipeline_id: int, pipeline_name: str, status: str = None) -> RunModel:
        """Create a new pipeline run"""
        session = self.get_session()
        try:
            run = RunModel(
                pipeline_id=pipeline_id,
                pipeline_name=pipeline_name,
                status=status or PipelineRunStatus.PENDING.value,
                created_at=datetime.utcnow()
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            logger.info(f"Created run {run.id} for pipeline '{pipeline_name}'")
            return run
        finally:
            session.close()

    def get_run(self, run_id: int) -> Optional[RunModel]:
        """Get run by ID"""
        session = self.get_session()
        try:
            return session.query(RunModel).filter(RunModel.id == run_id).first()
        finally:
            session.close()

    def update_run_status(self, run_id: int, status: str, error_message: str = None):
        """Update run status"""
        session = self.get_session()
        try:
            run = session.query(RunModel).filter(RunModel.id == run_id).first()
            if run:
                run.status = status
                if status == PipelineRunStatus.RUNNING.value:
                    run.start_time = datetime.utcnow()
                elif status in [PipelineRunStatus.SUCCEEDED.value, PipelineRunStatus.FAILED.value]:
                    run.end_time = datetime.utcnow()
                if error_message:
                    run.error_message = error_message
                session.commit()
                logger.info(f"Updated run {run_id} status to {status}")
        finally:
            session.close()

    def list_runs(self, pipeline_id: int = None, limit: int = 100) -> List[RunModel]:
        """List runs with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(RunModel)
            if pipeline_id:
                query = query.filter(RunModel.pipeline_id == pipeline_id)
            return query.order_by(RunModel.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def create_activity_execution(
        self,
        run_id: int,
        activity_name: str,
        activity_type: str
    ) -> ActivityExecutionModel:
        """Create an activity execution record"""
        session = self.get_session()
        try:
            execution = ActivityExecutionModel(
                run_id=run_id,
                activity_name=activity_name,
                activity_type=activity_type,
                status=PipelineRunStatus.PENDING.value,
                created_at=datetime.utcnow()
            )
            session.add(execution)
            session.commit()
            session.refresh(execution)
            return execution
        finally:
            session.close()

    def update_activity_execution(
        self,
        execution_id: int,
        status: str,
        output: dict = None,
        error_message: str = None
    ):
        """Update activity execution status"""
        session = self.get_session()
        try:
            execution = session.query(ActivityExecutionModel).filter(
                ActivityExecutionModel.id == execution_id
            ).first()
            if execution:
                execution.status = status
                if status == PipelineRunStatus.RUNNING.value:
                    execution.start_time = datetime.utcnow()
                elif status in [PipelineRunStatus.SUCCEEDED.value, PipelineRunStatus.FAILED.value]:
                    execution.end_time = datetime.utcnow()
                if output:
                    execution.output = output
                if error_message:
                    execution.error_message = error_message
                session.commit()
        finally:
            session.close()

    def get_activity_executions(self, run_id: int) -> List[ActivityExecutionModel]:
        """Get all activity executions for a run"""
        session = self.get_session()
        try:
            return session.query(ActivityExecutionModel).filter(
                ActivityExecutionModel.run_id == run_id
            ).all()
        finally:
            session.close()
