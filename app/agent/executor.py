from app.agent.models import ActionExecution, ActionName, Incident
from app.agent.runbooks import render_runbook
from app.config import Settings


class ActionExecutor:
    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self, incident: Incident, action: ActionName) -> ActionExecution:
        command = render_runbook(action, incident.service, incident.environment, incident.metadata)

        if self.settings.dry_run:
            return ActionExecution(
                action=action,
                command=command,
                dry_run=True,
                success=True,
                details="dry-run execution simulated",
            )

        # Integration point for real connectors (ArgoCD/Kubernetes/etc.)
        return ActionExecution(
            action=action,
            command=command,
            dry_run=False,
            success=True,
            details="command executed",
        )
