import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.integrations.composio_client import ComposioAdapter
from app.models.schemas import ActionReceipt, AuditCreated, AuditEvent, DatasetSummary, EvidenceRecord, TaskDecisionRequest, VerificationEvent, utc_now
from app.services.data_room import REQUIRED_FILENAMES, ingest_data_room, missing_required_files
from app.services.orchestrator import AuditOrchestrator
from app.services.store import store
from app.services.report import build_report
from app.integrations.clickhouse_client import ClickHouseAdapter
from app.settings import get_settings

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    settings = get_settings()
    orchestrator = AuditOrchestrator(settings)
    return {
        "status": "ok",
        "mode": "local",
        "demo_actions_enabled": settings.demo_actions_enabled,
        "integrations": [orchestrator.langfuse.status(), orchestrator.clickhouse.status(), orchestrator.composio.status(), orchestrator._anthropic_status()],
    }


@router.get("/data-room/preview")
async def data_room_preview():
    return {"documents": [], "evidence": [], "summary": DatasetSummary(), "required_files": REQUIRED_FILENAMES}


@router.post("/audits", response_model=AuditCreated)
async def create_audit(files: list[UploadFile] | None = File(default=None)):
    uploads = []
    for upload in (files or [])[:10]:
        content = await upload.read()
        if len(content) > 5_000_000:
            raise HTTPException(status_code=413, detail=f"{upload.filename} exceeds the 5 MB demo limit")
        uploads.append((upload.filename or "uploaded-document", content))
    missing = missing_required_files([filename for filename, _ in uploads])
    if missing:
        raise HTTPException(status_code=422, detail=f"Upload the complete evidence package. Missing: {', '.join(missing)}")
    ingestion = ingest_data_room(uploads, include_fixtures=False)
    run = store.create(ingestion.documents, ingestion.evidence, ingestion.summary)
    asyncio.create_task(AuditOrchestrator(get_settings()).run(run))
    return AuditCreated(audit_id=run.snapshot.audit_id, status=run.snapshot.status, events_url=f"/api/audits/{run.snapshot.audit_id}/events")


@router.get("/audits/{audit_id}")
async def get_audit(audit_id: UUID):
    run = store.get(audit_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit not found")
    return run.snapshot


@router.post("/audits/{audit_id}/tasks/{task_id}/decision")
async def decide_task(audit_id: UUID, task_id: str, request: TaskDecisionRequest):
    run = store.get(audit_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit not found")
    task = next((item for item in run.snapshot.recovery_tasks if item.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Recovery task not found")
    if task.status == "awaiting_verification":
        raise HTTPException(status_code=409, detail="Task is waiting for live Slack confirmation")
    if task.status not in {"pending_approval", "held"}:
        raise HTTPException(status_code=409, detail=f"Task decision is already {task.status}")

    receipts = ComposioAdapter(get_settings()).execute_task_decision(task, request.decision, request.note)
    task.status = {
        "approve": "executed" if receipts and all(item.status == "executed" for item in receipts) else "failed",
        "hold": "held",
        "reject": "rejected",
    }[request.decision]
    task.decision_note = request.note
    task.decided_at = utc_now()
    task.receipts = [item.id for item in receipts]
    run.snapshot.actions.extend(receipts)
    run.snapshot.report_markdown = build_report(run.snapshot)
    run.snapshot.analytics = ClickHouseAdapter(get_settings()).persist(run.snapshot)
    await run.publish(
        AuditEvent(
            step="decision",
            status="completed",
            message=f"{task.vendor} task {request.decision} decision processed",
            payload={"task": task.model_dump(mode="json"), "receipts": [item.model_dump(mode="json") for item in receipts]},
        )
    )
    return {"task": task, "receipts": receipts}


@router.post("/audits/{audit_id}/tasks/{task_id}/sync-verification")
async def sync_task_verification(audit_id: UUID, task_id: str):
    run = store.get(audit_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit not found")
    task = next((item for item in run.snapshot.recovery_tasks if item.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Recovery task not found")
    if not task.verification:
        raise HTTPException(status_code=409, detail="Task does not require Slack verification")
    if task.status != "awaiting_verification":
        return {"task": task, "receipts": [], "changed": False}

    adapter = ComposioAdapter(get_settings())
    prior = _verification_state(task.verification)
    receipts: list[ActionReceipt] = []
    if not task.verification.thread_ts:
        receipt, verification = adapter.request_figma_verification(str(audit_id))
        task.verification = verification
        _upsert_action(run.snapshot.actions, receipt)
        receipts.append(receipt)
    else:
        task.verification = adapter.sync_figma_verification(task.verification)

    if task.verification.interpretation:
        task.status = "pending_approval" if task.verification.interpretation == "reclaim" else "closed_no_action"
        evidence = EvidenceRecord(
            id="ev-figma-live-slack",
            document_id="slack-live-verification",
            vendor="Figma",
            claim="Resource owner confirmed whether the unused Figma workspace is still needed",
            locator=f"Slack thread {task.verification.thread_ts}",
            value=task.verification.response_text,
            confidence=1.0,
        )
        _upsert_evidence(run.snapshot.evidence, evidence)
        event = VerificationEvent(
            id=f"figma-verification-{task.verification.interpretation}",
            task_id=task.id,
            vendor=task.vendor,
            resource="Morgan Liu / Professional workspace",
            status=task.verification.status,
            response_text=task.verification.response_text,
            interpretation=task.verification.interpretation,
            thread_ts=task.verification.thread_ts,
            occurred_at=task.verification.responded_at or utc_now(),
        )
        _upsert_verification_event(run.snapshot.verification_events, event)
        response_receipt = ActionReceipt(
            id=f"figma-verification-{task.verification.interpretation}-receipt",
            kind="Slack verification response",
            title=f"Figma resource owner replied {task.verification.interpretation.upper()}",
            status="executed",
            tool="SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION",
            resource_id=task.verification.thread_ts,
            detail="Live Slack thread response interpreted as resource-owner evidence",
            payload={"response": task.verification.response_text, "interpretation": task.verification.interpretation},
        )
        _upsert_action(run.snapshot.actions, response_receipt)
        if response_receipt.id not in task.receipts:
            task.receipts.append(response_receipt.id)
        receipts.append(response_receipt)

    changed = prior != _verification_state(task.verification) or bool(receipts)
    if changed:
        run.snapshot.report_markdown = build_report(run.snapshot)
        run.snapshot.analytics = ClickHouseAdapter(get_settings()).persist(run.snapshot)
        await run.publish(
            AuditEvent(
                step="verification",
                status="completed" if task.verification.interpretation else "progress",
                message=_verification_message(task),
                payload={"task": task.model_dump(mode="json")},
            )
        )
    return {"task": task, "receipts": receipts, "changed": changed}


@router.post("/audits/{audit_id}/reset", response_model=AuditCreated)
async def reset_audit(audit_id: UUID):
    prior = store.get(audit_id)
    if not prior:
        raise HTTPException(status_code=404, detail="Audit not found")
    run = store.create(prior.snapshot.uploaded_documents, prior.snapshot.evidence, prior.snapshot.dataset_summary)
    asyncio.create_task(AuditOrchestrator(get_settings()).run(run))
    return AuditCreated(audit_id=run.snapshot.audit_id, status=run.snapshot.status, events_url=f"/api/audits/{run.snapshot.audit_id}/events")


@router.get("/audits/{audit_id}/report", response_class=PlainTextResponse)
async def get_report(audit_id: UUID):
    run = store.get(audit_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit not found")
    return PlainTextResponse(run.snapshot.report_markdown, media_type="text/markdown", headers={"Content-Disposition": 'attachment; filename="cited.md"'})


@router.get("/audits/{audit_id}/events")
async def events(audit_id: UUID):
    run = store.get(audit_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit not found")

    async def stream():
        for event in run.events:
            yield encode_event(event)
        if run.snapshot.status in {"completed", "failed"}:
            return
        queue: asyncio.Queue = asyncio.Queue()
        run.subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield encode_event(event)
                if event.step == "complete" or event.status == "failed":
                    break
        finally:
            run.subscribers.discard(queue)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/integrations/composio/connect/{toolkit}")
async def connect_composio(toolkit: str):
    try:
        url = ComposioAdapter(get_settings()).authorize(toolkit)
        return {"toolkit": toolkit, "redirect_url": url}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def encode_event(event: AuditEvent) -> str:
    return f"event: audit\ndata: {json.dumps(event.model_dump(mode='json'))}\n\n"


def _upsert_action(actions: list[ActionReceipt], receipt: ActionReceipt) -> None:
    actions[:] = [item for item in actions if item.id != receipt.id]
    actions.append(receipt)


def _upsert_evidence(evidence: list[EvidenceRecord], record: EvidenceRecord) -> None:
    evidence[:] = [item for item in evidence if item.id != record.id]
    evidence.append(record)


def _upsert_verification_event(events: list[VerificationEvent], event: VerificationEvent) -> None:
    events[:] = [item for item in events if item.id != event.id]
    events.append(event)


def _verification_message(task) -> str:
    if task.verification.status == "confirmed_reclaim":
        return "Figma owner replied RECLAIM. The final in-platform decision is now unlocked."
    if task.verification.status == "confirmed_keep":
        return "Figma owner replied KEEP. The recovery item was closed with no vendor action."
    if task.verification.status == "unrecognized":
        return "Slack reply received, but Margin is still waiting for RECLAIM or KEEP."
    if task.verification.status == "error":
        return "Slack verification check failed and will be retried."
    return "Margin is waiting for a reply in the Figma Slack verification thread."


def _verification_state(verification) -> tuple:
    return (
        verification.status,
        verification.thread_ts,
        verification.response_text,
        verification.interpretation,
        verification.error_detail,
    )
