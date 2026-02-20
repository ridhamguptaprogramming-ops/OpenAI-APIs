from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class IncidentTrigger(str, Enum):
    DEPLOY_FAILED = "deploy_failed"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    CRASH_LOOP = "crash_loop"


class IncidentStatus(str, Enum):
    OPEN = "open"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class ActionName(str, Enum):
    ROLLBACK = "rollback"
    RESTART = "restart"
    SCALE_UP = "scale_up"
    CLEAR_QUEUE = "clear_queue"
    REVERT_CONFIG = "revert_config"


class MetricSnapshot(BaseModel):
    service: str
    environment: str
    error_rate: float
    p95_latency_ms: int
    crash_looping: bool
    timestamp: datetime


class DeploySnapshot(BaseModel):
    service: str
    environment: str
    version: str
    commit_sha: str
    status: str
    timestamp: datetime


class ActionExecution(BaseModel):
    action: ActionName
    command: str
    dry_run: bool
    success: bool
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    service: str
    environment: str = "prod"
    trigger: IncidentTrigger
    summary: str
    severity: str = "medium"

    status: IncidentStatus = IncidentStatus.OPEN
    diagnosis: str | None = None
    confidence: float | None = None

    proposed_actions: list[ActionName] = Field(default_factory=list)
    executed_actions: list[ActionExecution] = Field(default_factory=list)

    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    metadata: dict[str, Any] = Field(default_factory=dict)
