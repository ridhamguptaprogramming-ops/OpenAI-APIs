from datetime import datetime, timezone

from app.agent.loop import SelfHealingAgent
from app.agent.models import IncidentStatus
from app.config import Settings
from app.schemas import DeployEventIn, MetricEventIn


def test_latency_incident_resolves_after_scale_up() -> None:
    settings = Settings(
        dry_run=True,
        allow_high_risk_actions=False,
        latency_p95_threshold_ms=500,
    )
    agent = SelfHealingAgent(settings)

    metric = MetricEventIn(
        service="checkout-api",
        environment="prod",
        error_rate=0.01,
        p95_latency_ms=1200,
        crash_looping=False,
        timestamp=datetime.now(timezone.utc),
    )

    incident_ids = agent.ingest_metric(metric)
    processed = agent.run_once(service="checkout-api")

    assert incident_ids
    assert processed
    assert processed[0].status == IncidentStatus.RESOLVED


def test_failed_deploy_escalates_when_high_risk_disabled() -> None:
    settings = Settings(
        dry_run=True,
        allow_high_risk_actions=False,
    )
    agent = SelfHealingAgent(settings)

    deploy = DeployEventIn(
        service="checkout-api",
        environment="prod",
        version="1.0.4",
        commit_sha="abcd1234",
        status="failed",
        timestamp=datetime.now(timezone.utc),
    )

    incident_ids = agent.ingest_deploy(deploy)
    processed = agent.run_once(service="checkout-api")

    assert incident_ids
    assert processed
    assert processed[0].status == IncidentStatus.ESCALATED
