import json
from pathlib import Path

from app.agent.models import Incident


class IncidentMemory:
    def __init__(self, log_path: str):
        self.path = Path(log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, incident: Incident) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(incident.model_dump(mode="json"), separators=(",", ":")) + "\n")

    def tail(self, limit: int = 50) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        selected = lines[-limit:]
        return [json.loads(line) for line in selected]
