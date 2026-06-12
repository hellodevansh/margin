import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.orchestrator import AuditOrchestrator
from app.settings import get_settings


def main():
    settings = get_settings()
    orchestrator = AuditOrchestrator(settings)
    checks = [
        check_langfuse(orchestrator),
        check_clickhouse(orchestrator),
        check_composio(orchestrator),
        check_anthropic(settings),
    ]
    payload = {
        "mode": "local",
        "demo_actions_enabled": settings.demo_actions_enabled,
        "integrations": checks,
    }
    print(json.dumps(payload, indent=2))
    return 0


def check_langfuse(orchestrator):
    status = orchestrator.langfuse.status().model_dump()
    if orchestrator.langfuse.client:
        try:
            if not orchestrator.langfuse.client.auth_check():
                raise RuntimeError("authentication rejected")
        except Exception as exc:
            status.update(state="degraded", detail=f"Credential check failed: {str(exc)[:120]}")
    return status


def check_clickhouse(orchestrator):
    status = orchestrator.clickhouse.status().model_dump()
    if orchestrator.clickhouse.client:
        try:
            if not orchestrator.clickhouse.client.ping():
                raise RuntimeError("ping returned false")
        except Exception as exc:
            status.update(state="degraded", detail=f"Credential check failed: {str(exc)[:120]}")
    return status


def check_composio(orchestrator):
    status = orchestrator.composio.status().model_dump()
    return status


def check_anthropic(settings):
    if not settings.anthropic_api_key:
        return {"name": "Anthropic", "state": "degraded", "detail": "No API key; deterministic fallback enabled"}
    try:
        import httpx

        with httpx.Client(trust_env=False, timeout=5.0) as client:
            response = client.get(
                f"{settings.anthropic_base_url.rstrip('/')}/v1/models",
                params={"limit": 1},
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            response.raise_for_status()
        return {"name": "Anthropic", "state": "connected", "detail": f"{settings.anthropic_model} credential verified"}
    except Exception as exc:
        return {"name": "Anthropic", "state": "degraded", "detail": f"Credential check failed: {str(exc)[:120]}"}


if __name__ == "__main__":
    raise SystemExit(main())
