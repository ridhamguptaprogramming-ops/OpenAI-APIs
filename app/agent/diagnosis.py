from app.agent.models import ActionName, DeploySnapshot, Incident, IncidentTrigger, MetricSnapshot


class Diagnoser:
    def diagnose(
        self,
        incident: Incident,
        metric: MetricSnapshot | None,
        deploy: DeploySnapshot | None,
    ) -> tuple[str, float, list[ActionName]]:
        trigger = incident.trigger

        if trigger == IncidentTrigger.DEPLOY_FAILED:
            return (
                "Latest deployment failed; suspect bad release artifact or configuration mismatch.",
                0.93,
                [ActionName.ROLLBACK, ActionName.REVERT_CONFIG],
            )

        if trigger == IncidentTrigger.CRASH_LOOP:
            return (
                "CrashLoopBackOff detected; likely startup regression or dependency unavailability.",
                0.88,
                [ActionName.RESTART, ActionName.ROLLBACK],
            )

        if trigger == IncidentTrigger.HIGH_ERROR_RATE:
            if deploy and deploy.status == "succeeded":
                return (
                    "Error rate spike after a successful deployment; suspect release-induced regression.",
                    0.84,
                    [ActionName.ROLLBACK, ActionName.RESTART],
                )
            return (
                "Error rate spike without clear deploy correlation; recycle workload first.",
                0.72,
                [ActionName.RESTART, ActionName.SCALE_UP],
            )

        if trigger == IncidentTrigger.HIGH_LATENCY:
            return (
                "p95 latency breach; likely saturation. Scale out before deeper remediation.",
                0.76,
                [ActionName.SCALE_UP, ActionName.RESTART],
            )

        return (
            "Undetermined incident type; apply conservative mitigation.",
            0.50,
            [ActionName.RESTART],
        )
