from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.agent.models import Incident


class DeployEventIn(BaseModel):
    service: str
    environment: str = "prod"
    version: str
    commit_sha: str
    status: Literal["started", "succeeded", "failed"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MetricEventIn(BaseModel):
    service: str
    environment: str = "prod"
    error_rate: float = Field(ge=0.0, le=1.0)
    p95_latency_ms: int = Field(ge=0)
    crash_looping: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestResponse(BaseModel):
    accepted: bool = True
    incident_ids: list[str] = Field(default_factory=list)
    processed_incidents: list[Incident] = Field(default_factory=list)


class RunOnceResponse(BaseModel):
    processed_incidents: list[Incident] = Field(default_factory=list)


class IncidentListResponse(BaseModel):
    incidents: list[Incident] = Field(default_factory=list)
