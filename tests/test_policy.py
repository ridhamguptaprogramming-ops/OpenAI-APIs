from app.agent.models import ActionName, Incident, IncidentTrigger
from app.agent.policy import SafetyPolicy
from app.config import Settings


def test_high_risk_action_blocked_by_default() -> None:
    settings = Settings(allow_high_risk_actions=False)
    policy = SafetyPolicy(settings)
    incident = Incident(
        service="payments-api",
        trigger=IncidentTrigger.DEPLOY_FAILED,
        summary="deploy failed",
    )

    decision = policy.evaluate(incident, ActionName.ROLLBACK)

    assert decision.allowed is False
    assert "high-risk" in decision.reason


def test_low_risk_action_allowed() -> None:
    settings = Settings(allow_high_risk_actions=False)
    policy = SafetyPolicy(settings)
    incident = Incident(
        service="payments-api",
        trigger=IncidentTrigger.HIGH_LATENCY,
        summary="latency high",
    )

    decision = policy.evaluate(incident, ActionName.SCALE_UP)

    assert decision.allowed is True
