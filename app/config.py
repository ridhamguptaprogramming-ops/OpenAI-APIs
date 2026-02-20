from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "self-healing-agent"
    dry_run: bool = True
    default_env: str = "prod"

    error_rate_threshold: float = 0.05
    latency_p95_threshold_ms: int = 800
    deploy_lookback_minutes: int = 20

    max_actions_per_incident: int = 2
    allow_high_risk_actions: bool = False
    enabled_runbooks: str = "rollback,restart,scale_up,clear_queue,revert_config"

    memory_log_path: str = ".agent/memory.jsonl"

    @property
    def enabled_runbook_set(self) -> set[str]:
        return {item.strip() for item in self.enabled_runbooks.split(",") if item.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
