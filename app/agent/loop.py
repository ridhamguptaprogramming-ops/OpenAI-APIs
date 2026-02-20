from datetime import datetime, timedelta, timezone
from threading import RLock

from app.agent.diagnosis import Diagnoser
from app.agent.executor import ActionExecutor
from app.agent.memory import IncidentMemory
from app.agent.models import (
    ActionName,
    DeploySnapshot,
    Incident,
    IncidentStatus,
    IncidentTrigger,
    MetricSnapshot,
)
from app.agent.policy import SafetyPolicy
from app.agent.verifier import Verifier
from app.config import Settings
from app.schemas import DeployEventIn, MetricEventIn


class SelfHealingAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.lock = RLock()

        self.latest_metrics: dict[str, MetricSnapshot] = {}
        self.latest_deploys: dict[str, DeploySnapshot] = {}
        self.incidents: dict[str, Incident] = {}

        self.diagnoser = Diagnoser()
        self.policy = SafetyPolicy(settings)
        self.executor = ActionExecutor(settings)
        self.verifier = Verifier(settings)
        self.memory = IncidentMemory(settings.memory_log_path)

    def ingest_deploy(self, event: DeployEventIn) -> list[str]:
        with self.lock:
            self.latest_deploys[event.service] = DeploySnapshot(
                service=event.service,
                environment=event.environment,
                version=event.version,
                commit_sha=event.commit_sha,
                status=event.status,
                timestamp=event.timestamp,
            )
            if event.status != "failed":
                return []

            incident = self._ensure_incident(
                service=event.service,
                environment=event.environment,
                trigger=IncidentTrigger.DEPLOY_FAILED,
                summary=f"Deployment failed for {event.service} ({event.version})",
                severity="high",
                metadata={"version": event.version, "commit_sha": event.commit_sha},
            )
            return [incident.id]

    def ingest_metric(self, event: MetricEventIn) -> list[str]:
        with self.lock:
            self.latest_metrics[event.service] = MetricSnapshot(
                service=event.service,
                environment=event.environment,
                error_rate=event.error_rate,
                p95_latency_ms=event.p95_latency_ms,
                crash_looping=event.crash_looping,
                timestamp=event.timestamp,
            )

            incident_ids: list[str] = []
            if event.crash_looping:
                incident = self._ensure_incident(
                    service=event.service,
                    environment=event.environment,
                    trigger=IncidentTrigger.CRASH_LOOP,
                    summary=f"Crash loop detected for {event.service}",
                    severity="high",
                )
                incident_ids.append(incident.id)

            if event.error_rate > self.settings.error_rate_threshold:
                incident = self._ensure_incident(
                    service=event.service,
                    environment=event.environment,
                    trigger=IncidentTrigger.HIGH_ERROR_RATE,
                    summary=f"Error rate breach for {event.service}: {event.error_rate:.3f}",
                    severity="high" if event.error_rate > (self.settings.error_rate_threshold * 2) else "medium",
                )
                incident_ids.append(incident.id)

            if event.p95_latency_ms > self.settings.latency_p95_threshold_ms:
                incident = self._ensure_incident(
                    service=event.service,
                    environment=event.environment,
                    trigger=IncidentTrigger.HIGH_LATENCY,
                    summary=f"Latency breach for {event.service}: p95={event.p95_latency_ms}ms",
                    severity="medium",
                )
                incident_ids.append(incident.id)

            return incident_ids

    def run_once(self, service: str | None = None) -> list[Incident]:
        with self.lock:
            now = datetime.now(timezone.utc)
            incidents = [
                incident
                for incident in self.incidents.values()
                if incident.status in {IncidentStatus.OPEN, IncidentStatus.MITIGATING}
                and (service is None or incident.service == service)
            ]
            processed: list[Incident] = []

            for incident in incidents:
                incident.status = IncidentStatus.MITIGATING
                incident.updated_at = now

                metric = self.latest_metrics.get(incident.service)
                deploy = self._recent_deploy(incident.service, now)

                diagnosis, confidence, actions = self.diagnoser.diagnose(incident, metric, deploy)
                incident.diagnosis = diagnosis
                incident.confidence = confidence
                incident.proposed_actions = actions

                recovered = False
                verification_note = "no action run"
                policy_reasons: list[str] = []

                for action in actions:
                    decision = self.policy.evaluate(incident, action)
                    if not decision.allowed:
                        policy_reasons.append(f"{action.value}: {decision.reason}")
                        continue

                    execution = self.executor.execute(incident, action)
                    incident.executed_actions.append(execution)

                    if execution.success and self.settings.dry_run:
                        self._simulate_metric_shift(incident.service, action)

                    current_metric = self.latest_metrics.get(incident.service)
                    recovered, verification_note = self.verifier.verify(incident, current_metric)
                    if recovered:
                        incident.status = IncidentStatus.RESOLVED
                        break

                if not recovered:
                    incident.status = IncidentStatus.ESCALATED

                if policy_reasons:
                    incident.metadata["policy_reasons"] = policy_reasons
                incident.metadata["verification"] = verification_note
                incident.updated_at = datetime.now(timezone.utc)

                self.memory.write(incident)
                processed.append(incident)

            return processed

    def list_incidents(self) -> list[Incident]:
        with self.lock:
            return sorted(self.incidents.values(), key=lambda item: item.opened_at, reverse=True)

    def get_incident(self, incident_id: str) -> Incident | None:
        with self.lock:
            return self.incidents.get(incident_id)

    def memory_tail(self, limit: int = 20) -> list[dict]:
        return self.memory.tail(limit)

    def _ensure_incident(
        self,
        service: str,
        environment: str,
        trigger: IncidentTrigger,
        summary: str,
        severity: str,
        metadata: dict | None = None,
    ) -> Incident:
        existing = self._find_open_incident(service, trigger)
        if existing:
            existing.summary = summary
            existing.severity = severity
            existing.updated_at = datetime.now(timezone.utc)
            if metadata:
                existing.metadata.update(metadata)
            return existing

        incident = Incident(
            service=service,
            environment=environment,
            trigger=trigger,
            summary=summary,
            severity=severity,
            metadata=metadata or {},
        )
        self.incidents[incident.id] = incident
        return incident

    def _find_open_incident(self, service: str, trigger: IncidentTrigger) -> Incident | None:
        for incident in self.incidents.values():
            if incident.service != service:
                continue
            if incident.trigger != trigger:
                continue
            if incident.status in {IncidentStatus.OPEN, IncidentStatus.MITIGATING}:
                return incident
        return None

    def _recent_deploy(self, service: str, now: datetime) -> DeploySnapshot | None:
        deploy = self.latest_deploys.get(service)
        if deploy is None:
            return None
        window_start = now - timedelta(minutes=self.settings.deploy_lookback_minutes)
        if deploy.timestamp >= window_start:
            return deploy
        return None

    def _simulate_metric_shift(self, service: str, action: ActionName) -> None:
        metric = self.latest_metrics.get(service)
        if metric is None:
            return

        if action in {ActionName.ROLLBACK, ActionName.REVERT_CONFIG}:
            metric.error_rate *= 0.3
            metric.p95_latency_ms = int(metric.p95_latency_ms * 0.6)
            metric.crash_looping = False
            return

        if action == ActionName.RESTART:
            metric.error_rate *= 0.6
            metric.p95_latency_ms = int(metric.p95_latency_ms * 0.85)
            metric.crash_looping = False
            return

        if action == ActionName.SCALE_UP:
            metric.p95_latency_ms = int(metric.p95_latency_ms * 0.6)
            metric.error_rate *= 0.9
            return

        if action == ActionName.CLEAR_QUEUE:
            metric.p95_latency_ms = int(metric.p95_latency_ms * 0.75)
