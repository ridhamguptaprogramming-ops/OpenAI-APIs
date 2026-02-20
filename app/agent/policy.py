from dataclasses import dataclass

from app.agent.models import ActionName, Incident
from app.agent.runbooks import RISK_LEVEL
from app.config import Settings


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


class SafetyPolicy:
    def __init__(self, settings: Settings):
        self.settings = settings

    def evaluate(self, incident: Incident, action: ActionName) -> PolicyDecision:
        if action.value not in self.settings.enabled_runbook_set:
            return PolicyDecision(False, f"action '{action.value}' is disabled")

        if len(incident.executed_actions) >= self.settings.max_actions_per_incident:
            return PolicyDecision(False, "incident action budget exceeded")

        risk = RISK_LEVEL[action]
        if risk == "high" and not self.settings.allow_high_risk_actions:
            return PolicyDecision(False, "high-risk action requires explicit enablement")

        return PolicyDecision(True, "allowed")
