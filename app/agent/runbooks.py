from app.agent.models import ActionName

RUNBOOK_TEMPLATES: dict[ActionName, str] = {
    ActionName.ROLLBACK: "argocd app rollback {service} --env {environment}",
    ActionName.RESTART: "kubectl rollout restart deploy/{service} -n {environment}",
    ActionName.SCALE_UP: "kubectl scale deploy/{service} -n {environment} --replicas={replicas}",
    ActionName.CLEAR_QUEUE: "queuectl purge --service {service} --env {environment}",
    ActionName.REVERT_CONFIG: "configctl revert --service {service} --env {environment}",
}

RISK_LEVEL: dict[ActionName, str] = {
    ActionName.ROLLBACK: "high",
    ActionName.RESTART: "medium",
    ActionName.SCALE_UP: "medium",
    ActionName.CLEAR_QUEUE: "low",
    ActionName.REVERT_CONFIG: "high",
}


def render_runbook(action: ActionName, service: str, environment: str, metadata: dict | None = None) -> str:
    template = RUNBOOK_TEMPLATES[action]
    context = {"service": service, "environment": environment, "replicas": 5}
    if metadata:
        context.update(metadata)
    return template.format(**context)
