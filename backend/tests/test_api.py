from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ActionReceipt, TaskVerification
from app.services.store import store
from app.services.tasks import build_recovery_tasks
from app.services.data_room import FIXTURE_DIR, REQUIRED_FILENAMES


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def no_run(_self, _run):
    return None


def test_create_audit(monkeypatch):
    monkeypatch.setattr("app.api.routes.AuditOrchestrator.run", no_run)
    response = client.post("/api/audits", files=demo_package())
    assert response.status_code == 200
    assert response.json()["audit_id"]


def test_data_room_preview_and_upload(monkeypatch):
    monkeypatch.setattr("app.api.routes.AuditOrchestrator.run", no_run)
    preview = client.get("/api/data-room/preview")
    assert preview.status_code == 200
    assert preview.json()["summary"]["documents"] == 0
    assert preview.json()["summary"]["records"] == 0
    assert len(preview.json()["required_files"]) == 7

    incomplete = client.post("/api/audits", files={"files": ("supplement.csv", b"vendor,value\nExample,42\n", "text/csv")})
    assert incomplete.status_code == 422

    response = client.post("/api/audits", files=demo_package())
    assert response.status_code == 200


def test_audit_rejects_empty_data_room(monkeypatch):
    monkeypatch.setattr("app.api.routes.AuditOrchestrator.run", no_run)
    response = client.post("/api/audits")
    assert response.status_code == 422
    assert "Upload the complete evidence package" in response.json()["detail"]


def test_project_head_approval_endpoint_executes_outlook_only(monkeypatch):
    run = store.create()
    run.snapshot.recovery_tasks = build_recovery_tasks()

    class FakeComposio:
        def __init__(self, _settings):
            pass

        def execute_task_decision(self, task, decision, note):
            assert task.id == "datadog-contract-review"
            assert decision == "approve"
            assert note == "Proceed this week"
            return [
                ActionReceipt(id="outlook-receipt", kind="Outlook follow-up", title="Draft created", status="executed", tool="OUTLOOK_CREATE_DRAFT", detail="Draft created"),
            ]

    class FakeClickHouse:
        def __init__(self, _settings):
            pass

        def persist(self, snapshot):
            return snapshot.analytics

    monkeypatch.setattr("app.api.routes.ComposioAdapter", FakeComposio)
    monkeypatch.setattr("app.api.routes.ClickHouseAdapter", FakeClickHouse)
    response = client.post(
        f"/api/audits/{run.snapshot.audit_id}/tasks/datadog-contract-review/decision",
        json={"decision": "approve", "note": "Proceed this week"},
    )
    assert response.status_code == 200
    assert response.json()["task"]["status"] == "executed"
    assert [receipt["tool"] for receipt in response.json()["receipts"]] == ["OUTLOOK_CREATE_DRAFT"]


def test_hold_decision_records_in_platform_without_external_receipt(monkeypatch):
    run = store.create()
    run.snapshot.recovery_tasks = build_recovery_tasks()

    class FakeComposio:
        def __init__(self, _settings):
            pass

        def execute_task_decision(self, task, decision, note):
            assert decision == "hold"
            return []

    class FakeClickHouse:
        def __init__(self, _settings):
            pass

        def persist(self, snapshot):
            return snapshot.analytics

    monkeypatch.setattr("app.api.routes.ComposioAdapter", FakeComposio)
    monkeypatch.setattr("app.api.routes.ClickHouseAdapter", FakeClickHouse)
    response = client.post(
        f"/api/audits/{run.snapshot.audit_id}/tasks/slack-seat-recovery/decision",
        json={"decision": "hold", "note": "Review next week"},
    )
    assert response.status_code == 200
    assert response.json()["task"]["status"] == "held"
    assert response.json()["receipts"] == []


def test_figma_approval_is_rejected_before_live_slack_confirmation():
    run = live_figma_run()
    response = client.post(
        f"/api/audits/{run.snapshot.audit_id}/tasks/figma-renewal-stop/decision",
        json={"decision": "approve", "note": ""},
    )
    assert response.status_code == 409
    assert "waiting for live Slack confirmation" in response.json()["detail"]


def test_live_slack_reclaim_unlocks_figma_idempotently(monkeypatch):
    run = live_figma_run()

    class FakeComposio:
        def __init__(self, _settings):
            pass

        def sync_figma_verification(self, verification):
            verification.status = "confirmed_reclaim"
            verification.response_text = "RECLAIM"
            verification.interpretation = "reclaim"
            return verification

    class FakeClickHouse:
        def __init__(self, _settings):
            pass

        def persist(self, snapshot):
            return snapshot.analytics

    monkeypatch.setattr("app.api.routes.ComposioAdapter", FakeComposio)
    monkeypatch.setattr("app.api.routes.ClickHouseAdapter", FakeClickHouse)
    endpoint = f"/api/audits/{run.snapshot.audit_id}/tasks/figma-renewal-stop/sync-verification"
    response = client.post(endpoint)
    assert response.status_code == 200
    assert response.json()["task"]["status"] == "pending_approval"
    assert response.json()["task"]["verification"]["status"] == "confirmed_reclaim"
    assert sum(item.id == "ev-figma-live-slack" for item in run.snapshot.evidence) == 1
    assert sum(item.id == "figma-verification-reclaim" for item in run.snapshot.verification_events) == 1

    repeated = client.post(endpoint)
    assert repeated.status_code == 200
    assert repeated.json()["changed"] is False
    assert sum(item.id == "ev-figma-live-slack" for item in run.snapshot.evidence) == 1


def test_live_slack_keep_closes_figma_without_vendor_action(monkeypatch):
    run = live_figma_run()

    class FakeComposio:
        def __init__(self, _settings):
            pass

        def sync_figma_verification(self, verification):
            verification.status = "confirmed_keep"
            verification.response_text = "KEEP"
            verification.interpretation = "keep"
            return verification

    class FakeClickHouse:
        def __init__(self, _settings):
            pass

        def persist(self, snapshot):
            return snapshot.analytics

    monkeypatch.setattr("app.api.routes.ComposioAdapter", FakeComposio)
    monkeypatch.setattr("app.api.routes.ClickHouseAdapter", FakeClickHouse)
    response = client.post(f"/api/audits/{run.snapshot.audit_id}/tasks/figma-renewal-stop/sync-verification")
    assert response.status_code == 200
    assert response.json()["task"]["status"] == "closed_no_action"
    assert not any(item.tool == "OUTLOOK_CREATE_DRAFT" for item in run.snapshot.actions)


def live_figma_run():
    run = store.create()
    run.snapshot.recovery_tasks = build_recovery_tasks(
        figma_verification=TaskVerification(
            status="awaiting_reply",
            channel_id="C123",
            thread_ts="123.456",
            prompt="Reply RECLAIM or KEEP",
        )
    )
    return run


def demo_package():
    return [
        ("files", (filename, (FIXTURE_DIR / filename).read_bytes(), "application/json" if filename.endswith(".json") else "text/csv"))
        for filename in REQUIRED_FILENAMES
    ]
