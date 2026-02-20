# Self-Healing AI DevOps Agent (MVP)

A minimal autonomous DevOps agent that follows:

`observe -> diagnose -> plan -> execute -> verify -> learn`

This MVP focuses on **safe automated mitigation** with deterministic runbooks and dry-run execution by default.

## What this does

- Accepts deploy + metric events via API.
- Detects incident triggers (deploy failure, high error rate, high latency, crash loop).
- Diagnoses with rule-based logic.
- Chooses from approved runbooks only (no free-form shell generation).
- Enforces policy constraints (enabled actions, risk gating, action budget).
- Executes in dry-run mode by default.
- Verifies service recovery against SLO thresholds.
- Stores incident timeline in memory log.

## Repo structure

```text
app/
  main.py                 # FastAPI entrypoint
  config.py               # Runtime settings
  schemas.py              # API contracts
  agent/
    models.py             # Domain models
    runbooks.py           # Deterministic runbook templates
    diagnosis.py          # Rule-based diagnosis engine
    policy.py             # Safety policy / guardrails
    executor.py           # Action execution adapter
    verifier.py           # Post-action recovery checks
    memory.py             # Incident memory log
    loop.py               # Core autonomous agent loop
  connectors/
    k8s.py                # Placeholder Kubernetes connector
    observability.py      # Placeholder metrics connector
    chatops.py            # Placeholder Slack/Teams connector

tests/
  test_policy.py
  test_loop.py
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000/docs`

## API contracts (MVP)

### 1) Deploy events

`POST /events/deploy`

```json
{
  "service": "payments-api",
  "environment": "prod",
  "version": "1.15.0",
  "commit_sha": "d1e2f3a",
  "status": "failed",
  "timestamp": "2026-02-20T17:00:00Z"
}
```

### 2) Metric events

`POST /events/metric`

```json
{
  "service": "payments-api",
  "environment": "prod",
  "error_rate": 0.13,
  "p95_latency_ms": 1450,
  "crash_looping": true,
  "timestamp": "2026-02-20T17:01:00Z"
}
```

### 3) Manually run one loop

`POST /agent/run-once?service=payments-api`

### 4) Inspect incidents

- `GET /incidents`
- `GET /incidents/{incident_id}`

## Safety defaults

- `DRY_RUN=true`
- High-risk actions (`rollback`, `revert_config`) blocked unless `ALLOW_HIGH_RISK_ACTIONS=true`.
- Max actions per incident bounded by `MAX_ACTIONS_PER_INCIDENT`.

## Suggested production-hardening steps

1. Replace placeholder connectors with real ArgoCD/Kubernetes/Datadog integrations.
2. Add queue + worker (Redis/Celery or Kafka consumer) for async event processing.
3. Add OPA policy evaluation before each action.
4. Add approval workflow for high-risk actions in Slack.
5. Add persistent incident store (PostgreSQL) + analytics dashboard.
