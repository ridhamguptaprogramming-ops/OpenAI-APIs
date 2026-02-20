from fastapi import FastAPI, HTTPException, Query

from app.agent.loop import SelfHealingAgent
from app.config import get_settings
from app.schemas import DeployEventIn, IncidentListResponse, IngestResponse, MetricEventIn, RunOnceResponse

settings = get_settings()
agent = SelfHealingAgent(settings)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/events/deploy", response_model=IngestResponse)
def ingest_deploy(event: DeployEventIn) -> IngestResponse:
    incident_ids = agent.ingest_deploy(event)
    processed = agent.run_once(service=event.service)
    return IngestResponse(incident_ids=incident_ids, processed_incidents=processed)


@app.post("/events/metric", response_model=IngestResponse)
def ingest_metric(event: MetricEventIn) -> IngestResponse:
    incident_ids = agent.ingest_metric(event)
    processed = agent.run_once(service=event.service)
    return IngestResponse(incident_ids=incident_ids, processed_incidents=processed)


@app.post("/agent/run-once", response_model=RunOnceResponse)
def run_once(service: str | None = Query(default=None)) -> RunOnceResponse:
    processed = agent.run_once(service=service)
    return RunOnceResponse(processed_incidents=processed)


@app.get("/incidents", response_model=IncidentListResponse)
def list_incidents() -> IncidentListResponse:
    return IncidentListResponse(incidents=agent.list_incidents())


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = agent.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    return incident


@app.get("/memory")
def memory(limit: int = Query(default=20, ge=1, le=500)) -> dict[str, list[dict]]:
    return {"items": agent.memory_tail(limit)}
