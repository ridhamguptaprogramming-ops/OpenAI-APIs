from app.agent.models import MetricSnapshot


class ObservabilityClient:
    """Placeholder for Prometheus/Datadog queries."""

    def latest_metric(self, service: str) -> MetricSnapshot | None:
        _ = service
        return None
