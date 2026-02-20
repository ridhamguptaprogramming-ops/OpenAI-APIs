from app.agent.models import Incident, IncidentTrigger, MetricSnapshot
from app.config import Settings


class Verifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    def verify(self, incident: Incident, metric: MetricSnapshot | None) -> tuple[bool, str]:
        if incident.trigger == IncidentTrigger.DEPLOY_FAILED:
            # For deploy failures, a successful rollback/revert runbook is treated as recovered.
            if incident.executed_actions and incident.executed_actions[-1].success:
                return True, "deploy failure mitigated by runbook"
            return False, "deploy incident not yet mitigated"

        if metric is None:
            return False, "no metric snapshot available"

        if incident.trigger == IncidentTrigger.HIGH_ERROR_RATE:
            if metric.error_rate <= self.settings.error_rate_threshold:
                return True, "error rate recovered"
            return False, f"error rate still high ({metric.error_rate:.3f})"

        if incident.trigger == IncidentTrigger.HIGH_LATENCY:
            if metric.p95_latency_ms <= self.settings.latency_p95_threshold_ms:
                return True, "latency recovered"
            return False, f"latency still high ({metric.p95_latency_ms}ms)"

        if incident.trigger == IncidentTrigger.CRASH_LOOP:
            if not metric.crash_looping:
                return True, "crash loop resolved"
            return False, "workload still crash looping"

        return False, "unsupported incident trigger"
