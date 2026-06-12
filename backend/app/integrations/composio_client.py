import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from app.models.schemas import ActionReceipt, IntegrationStatus, RecoveryTask, TaskVerification
from app.settings import Settings


TOOLKIT_VERSIONS = {
    "slack": "20260519_01",
    "outlook": "20260524_00",
}

FIGMA_VERIFICATION_PROMPT = """**Margin resource verification — Figma Professional workspace**

Our usage review found that Morgan Liu's Figma Professional workspace has **0 active days in the last 90 days**. The employee roster also marks Morgan as departed. The workspace costs **$7,200 annually**.

Please reply in this thread with exactly one response:
- `RECLAIM` — confirm the workspace is no longer needed
- `KEEP` — confirm the workspace must remain active

This reply supplies resource-owner evidence only. Final approval and vendor action happen inside Margin."""


class ComposioAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.composio_api_key:
            try:
                from composio import Composio

                self.client = Composio(api_key=settings.composio_api_key)
            except Exception:
                self.client = None

    def status(self) -> IntegrationStatus:
        if not self.client:
            return IntegrationStatus(name="Composio", state="degraded", detail="Slack usage verification and Outlook execution unavailable")
        try:
            accounts = self.client.connected_accounts.list(
                user_ids=[self.settings.composio_user_id],
                statuses=["ACTIVE"],
                toolkit_slugs=["slack", "outlook"],
                limit=100,
            )
            connected = {
                getattr(getattr(account, "toolkit", None), "slug", None)
                or getattr(account, "toolkit_slug", None)
                for account in getattr(accounts, "items", [])
            }
            missing = []
            if "slack" not in connected:
                missing.append("Slack connection")
            if "outlook" not in connected:
                missing.append("Outlook connection")
            if not self.settings.slack_channel_id:
                missing.append("Slack verification channel")
            if missing:
                return IntegrationStatus(name="Composio", state="degraded", detail=f"Missing: {', '.join(missing)}")
            if self.settings.demo_actions_enabled:
                return IntegrationStatus(name="Composio", state="connected", detail="Live Slack usage verification and Outlook execution enabled")
            return IntegrationStatus(name="Composio", state="degraded", detail="Slack verification and Outlook execution ready; live action switch disabled")
        except Exception:
            return IntegrationStatus(name="Composio", state="degraded", detail="Account status check failed")

    def authorize(self, toolkit: str) -> str:
        if not self.client:
            raise RuntimeError("Composio API key is not configured")
        session = self.client.create(user_id=self.settings.composio_user_id, manage_connections=False)
        return session.authorize(toolkit).redirect_url

    def request_figma_verification(self, audit_id: str) -> tuple[ActionReceipt, TaskVerification]:
        prompt = f"{FIGMA_VERIFICATION_PROMPT}\n\nAudit `{audit_id}`"
        receipt = self._execute(
            action_id="figma-resource-verification",
            kind="Slack usage verification",
            title="Figma owner confirmation requested",
            tool="SLACK_CHAT_POST_MESSAGE",
            arguments={
                "channel": self.settings.slack_channel_id,
                "markdown_text": prompt,
            },
            success_detail="Live Figma resource-verification request posted to Slack",
        )
        ready = receipt.status == "executed" and bool(receipt.resource_id)
        verification = TaskVerification(
            status="awaiting_reply" if ready else "error",
            channel_id=self.settings.slack_channel_id,
            thread_ts=receipt.resource_id if ready else None,
            posted_receipt_id=receipt.id,
            prompt=prompt,
            posted_at=_now(),
            error_detail="" if ready else receipt.detail,
        )
        return receipt, verification

    def sync_figma_verification(self, verification: TaskVerification) -> TaskVerification:
        updated = deepcopy(verification)
        updated.checked_at = _now()
        if not self.client or not self.settings.demo_actions_enabled:
            updated.status = "error"
            updated.error_detail = "Live Slack reply checking is unavailable"
            return updated
        if not updated.thread_ts:
            updated.status = "error"
            updated.error_detail = "Slack verification message has no thread timestamp"
            return updated
        try:
            result = self.client.tools.execute(
                "SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION",
                user_id=self.settings.composio_user_id,
                arguments={"channel": updated.channel_id or self.settings.slack_channel_id, "ts": updated.thread_ts},
                version=TOOLKIT_VERSIONS["slack"],
            )
            response = latest_human_thread_reply(result, updated.thread_ts)
            if not response:
                updated.status = "awaiting_reply"
                updated.error_detail = ""
                return updated
            updated.response_text = response
            updated.responded_at = _now()
            updated.error_detail = ""
            interpretation = interpret_verification_reply(response)
            updated.interpretation = interpretation
            updated.status = {
                "reclaim": "confirmed_reclaim",
                "keep": "confirmed_keep",
                None: "unrecognized",
            }[interpretation]
            return updated
        except Exception as exc:
            updated.status = "error"
            updated.error_detail = f"Slack reply check failed: {str(exc)[:180]}"
            return updated

    def execute_task_decision(self, task: RecoveryTask, decision: str, note: str = "") -> list[ActionReceipt]:
        if decision != "approve":
            return []

        subject, body = self._outlook_content(task, note)
        outlook = self._execute(
            action_id=f"{task.id}-outlook",
            kind="Vendor negotiation draft",
            title=f"Actionable {task.vendor} vendor draft created",
            tool="OUTLOOK_CREATE_DRAFT",
            arguments={
                "to_recipients": [task.draft_to],
                "subject": subject,
                "body": body,
            },
            success_detail=f"Live vendor-facing Outlook draft created for {task.draft_to}",
        )
        return [outlook]

    def _outlook_content(self, task: RecoveryTask, note: str) -> tuple[str, str]:
        body = task.draft_body
        if note:
            body = f"{body}\n\nAdditional instruction from AcmeAI: {note}"
        return task.draft_subject, body

    def _execute(self, action_id: str, kind: str, title: str, tool: str, arguments: dict, success_detail: str) -> ActionReceipt:
        if not self.client or not self.settings.demo_actions_enabled:
            reason = "External execution unavailable" if not self.client else "Execution blocked by DEMO_ACTIONS_ENABLED=false"
            return ActionReceipt(id=action_id, kind=kind, title=title, status="simulated", tool=tool, resource_id=f"demo_{uuid4().hex[:8]}", detail=reason, payload=arguments)
        try:
            toolkit = tool.split("_", 1)[0].lower()
            result = self.client.tools.execute(
                tool,
                user_id=self.settings.composio_user_id,
                arguments=arguments,
                version=TOOLKIT_VERSIONS[toolkit],
            )
            resource_id = _resource_id(result) or f"composio_{uuid4().hex[:8]}"
            return ActionReceipt(id=action_id, kind=kind, title=title, status="executed", tool=tool, resource_id=resource_id, detail=success_detail, payload=arguments)
        except Exception as exc:
            return ActionReceipt(id=action_id, kind=kind, title=title, status="failed", tool=tool, detail=f"Composio execution failed: {str(exc)[:180]}", payload=arguments)


def _resource_id(result) -> str:
    if isinstance(result, dict):
        data = result.get("data") or {}
        return str(data.get("ts") or data.get("id") or data.get("webLink") or "")
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return str(data.get("ts") or data.get("id") or data.get("webLink") or "")
    return str(getattr(result, "id", "") or "")


def interpret_verification_reply(text: str) -> str | None:
    commands = re.findall(r"\b(RECLAIM|KEEP)\b", text.upper())
    return commands[0].lower() if len(set(commands)) == 1 else None


def latest_human_thread_reply(result, parent_ts: str) -> str:
    messages = _messages_from_result(result)
    replies = [
        message
        for message in messages
        if str(message.get("ts") or "") != parent_ts
        and not message.get("bot_id")
        and message.get("subtype") not in {"bot_message", "message_changed", "message_deleted"}
        and str(message.get("text") or "").strip()
    ]
    replies.sort(key=lambda message: _slack_timestamp(message.get("ts")))
    return str(replies[-1].get("text") or "").strip() if replies else ""


def _messages_from_result(result) -> list[dict]:
    data = result.get("data", result) if isinstance(result, dict) else getattr(result, "data", {})
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return []
    while isinstance(data, dict) and "messages" not in data and isinstance(data.get("data"), dict):
        data = data["data"]
    messages = data.get("messages", []) if isinstance(data, dict) else []
    return [message for message in messages if isinstance(message, dict)]


def _slack_timestamp(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _now() -> datetime:
    return datetime.now(timezone.utc)
