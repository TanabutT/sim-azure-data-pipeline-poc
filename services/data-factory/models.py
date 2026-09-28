from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class ActivityType(str, Enum):
    COPY = "CopyActivity"
    SPARK = "SparkActivity"
    WAIT = "WaitActivity"
    WEB = "WebActivity"
    IF_CONDITION = "IfConditionActivity"


class PipelineRunStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class Activity(BaseModel):
    name: str
    type: ActivityType
    config: Dict[str, Any]
    dependsOn: Optional[List[str]] = None


class Pipeline(BaseModel):
    name: str
    description: Optional[str] = None
    activities: List[Activity]
    triggers: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class PipelineRun(BaseModel):
    id: Optional[int] = None
    pipeline_id: Optional[int] = None
    pipeline_name: Optional[str] = None
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class ActivityExecution(BaseModel):
    id: Optional[int] = None
    run_id: Optional[int] = None
    activity_name: str
    activity_type: ActivityType
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class LinkedService(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any]


class DatasetSchema(BaseModel):
    name: str
    type: str
    linked_service: str
    structure: Optional[List[Dict[str, str]]] = None
    properties: Dict[str, Any]


class RunTrigger(str, Enum):
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"
    EVENT = "Event"


class PipelineRunRequest(BaseModel):
    pipeline_name: str
    trigger: RunTrigger = RunTrigger.MANUAL
    parameters: Optional[Dict[str, Any]] = None
