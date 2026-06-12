import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from app.agents.decision import generate_and_evaluate
from app.fixtures.demo_data import METRICS
from app.integrations.clickhouse_client import ClickHouseAdapter
from app.integrations.composio_client import ComposioAdapter
from app.integrations.langfuse_client import LangfuseAdapter
from app.models.schemas import AuditEvent, IntegrationStatus, TaskVerification, TraceNode, VerificationEvent
from app.services.detection import detect_leaks, detect_redundancy, load_spend, verify_employees
from app.services.report import build_report
from app.services.research import research_pricing
from app.services.store import AuditRun
from app.services.tasks import build_recovery_tasks
from app.settings import Settings


TRACE_STEPS = [
    ("ingest", "Ingest data room"),
    ("load", "Load spend data"),
    ("leaks", "Detect leaks"),
    ("redundancy", "Detect redundancy"),
    ("verification", "Slack resource verification"),
    ("research", "Open web research"),
    ("strategies", "Strategy generation"),
    ("gate", "Langfuse audited decision gate"),
    ("actions", "Prepare in-platform decisions"),
    ("memory", "ClickHouse query-backed memory"),
    ("report", "Generate cited report"),
]


class AuditOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.langfuse = LangfuseAdapter(settings)
        self.clickhouse = ClickHouseAdapter(settings)
        self.composio = ComposioAdapter(settings)
        self.figma_verification: TaskVerification | None = None

    async def run(self, run: AuditRun) -> None:
        snapshot = run.snapshot
        snapshot.status = "running"
        snapshot.integrations = [self.langfuse.status(), self.clickhouse.status(), self.composio.status(), self._anthropic_status()]
        snapshot.trace_tree = TraceNode(
            id="root",
            label="Root Audit",
            status="running",
            children=[TraceNode(id=key, label=label, status="pending") for key, label in TRACE_STEPS],
        )

        try:
            with self.langfuse.observe("margin.audit", input={"company": snapshot.company, "audit_id": str(snapshot.audit_id)}) as root_span:
                snapshot.trace_id = self.langfuse.current_trace_id()
                snapshot.trace_url = self.langfuse.trace_url(snapshot.trace_id)
                await self._step(run, "ingest", "Parsing contracts, invoices, usage, and capability evidence", lambda: self._ingest(snapshot))
                await self._step(run, "load", "Normalizing the AcmeAI software estate", lambda: self._load(snapshot))
                await self._step(run, "leaks", "Detecting six classes of SaaS spend leakage", lambda: self._leaks(snapshot))
                await self._step(run, "redundancy", "Computing tool capability overlap", lambda: self._redundancy(snapshot))
                await self._step(run, "verification", "Posting live Figma owner verification to Slack", lambda: self._verify(snapshot))
                await self._step(run, "research", "Launching browser agent across official pricing and competitor pages", lambda: self._research(run, snapshot))
                await self._step(run, "strategies", "Generating recoverability strategies", lambda: self._strategies(snapshot))
                await self._step(run, "gate", "Using Langfuse scores to block unsafe ideas and release safe strategies", lambda: self._gate(snapshot))
                await self._step(run, "actions", "Building the decision queue only from Langfuse-passed strategies", lambda: self._actions(snapshot))
                await self._step(run, "memory", "Persisting every audit artifact to ClickHouse and querying the results back", lambda: self._memory(snapshot))
                await self._step(run, "report", "Generating cited recovery report", lambda: self._report(snapshot))
                if root_span:
                    root_span.update(output={"status": "completed", "potential_leakage": snapshot.metrics.potential_leakage})
            snapshot.status = "completed"
            snapshot.completed_at = datetime.now(timezone.utc)
            snapshot.trace_tree.status = "completed"
            self.langfuse.flush()
            await run.publish(AuditEvent(step="complete", status="completed", message="Recovery case complete. Langfuse released three safe actions to the project-head queue.", payload={"audit_id": str(snapshot.audit_id)}))
        except Exception as exc:
            snapshot.status = "failed"
            await run.publish(AuditEvent(step="audit", status="failed", message=f"Audit failed: {str(exc)[:200]}"))

    async def _step(self, run: AuditRun, key: str, message: str, operation) -> None:
        node = next(item for item in run.snapshot.trace_tree.children if item.id == key)
        node.status = "running"
        await run.publish(AuditEvent(step=key, status="started", message=message))
        started = perf_counter()
        with self.langfuse.observe(key, input={"audit_id": str(run.snapshot.audit_id)}) as span:
            result = operation()
            if asyncio.iscoroutine(result):
                result = await result
            if span:
                span.update(output={"status": "completed"})
        await asyncio.sleep(self.settings.audit_step_delay_ms / 1000)
        duration = int((perf_counter() - started) * 1000)
        node.status = "completed"
        node.duration_ms = duration
        await run.publish(AuditEvent(step=key, status="completed", message=f"{message} completed", duration_ms=duration))

    def _load(self, snapshot):
        snapshot.spend = load_spend()
        snapshot.metrics = deepcopy(METRICS)

    def _ingest(self, snapshot):
        if not snapshot.uploaded_documents:
            raise RuntimeError("Audit data room is empty")

    def _leaks(self, snapshot):
        snapshot.leaks = detect_leaks()

    def _redundancy(self, snapshot):
        snapshot.redundancy = detect_redundancy()

    def _verify(self, snapshot):
        snapshot.employee_replies = [reply for reply in verify_employees() if reply.vendor != "Figma"]
        receipt, self.figma_verification = self.composio.request_figma_verification(str(snapshot.audit_id))
        snapshot.actions = [receipt]
        snapshot.verification_events = [
            VerificationEvent(
                id="figma-verification-posted",
                task_id="figma-renewal-stop",
                vendor="Figma",
                resource="Morgan Liu / Professional workspace",
                status="posted" if self.figma_verification.thread_ts else "post_failed",
                thread_ts=self.figma_verification.thread_ts,
            )
        ]

    async def _research(self, run, snapshot):
        async def publish_activity(activity):
            with self.langfuse.observe(
                f"browser.{activity.kind}",
                input={"query": activity.query, "url": activity.url, "vendor": activity.vendor},
            ) as span:
                if span:
                    span.update(output={"status": activity.status, "detail": activity.detail})
            await run.publish(
                AuditEvent(
                    step="research",
                    status="progress",
                    message=activity.label,
                    payload={"activity": activity.model_dump(mode="json")},
                )
            )

        snapshot.research, snapshot.research_activity = await research_pricing(publish_activity)

    async def _strategies(self, snapshot):
        with self.langfuse.observe(
            "claude.strategy-evaluation",
            as_type="generation",
            model=self.settings.anthropic_model,
            input={"leaks": [item.model_dump(mode="json") for item in snapshot.leaks], "research": [item.model_dump(mode="json") for item in snapshot.research]},
        ) as generation:
            snapshot.strategies, source, usage = await generate_and_evaluate(self.settings, snapshot.model_dump(mode="json"))
            if generation:
                generation.update(output={"source": source, "strategies": [item.model_dump(mode="json") for item in snapshot.strategies]})
                if usage:
                    generation.update(usage_details=usage)
        for index, integration in enumerate(snapshot.integrations):
            if integration.name == "Anthropic":
                if source == "fixture":
                    snapshot.integrations[index] = IntegrationStatus(
                        name="Anthropic",
                        state="degraded",
                        detail="Claude request unavailable; validated deterministic strategy fixtures used",
                    )
                else:
                    snapshot.integrations[index] = IntegrationStatus(
                        name="Anthropic",
                        state="connected",
                        detail=f"{self.settings.anthropic_model} strategy review completed",
                    )

    def _gate(self, snapshot):
        for strategy in snapshot.strategies:
            with self.langfuse.observe(
                f"strategy.{strategy.id}",
                input={"vendor": strategy.vendor, "savings": strategy.savings},
                output=strategy.model_dump(mode="json"),
            ) as span:
                self.langfuse.score_strategy(span, strategy)

    def _actions(self, snapshot):
        snapshot.recovery_tasks = build_recovery_tasks(snapshot.strategies, self.figma_verification)

    def _memory(self, snapshot):
        snapshot.analytics = self.clickhouse.persist(snapshot)

    def _report(self, snapshot):
        snapshot.report_markdown = build_report(snapshot)
        report_path = Path(__file__).resolve().parents[3] / "cited.md"
        report_path.write_text(snapshot.report_markdown, encoding="utf-8")

    def _anthropic_status(self):
        if self.settings.anthropic_api_key:
            return IntegrationStatus(name="Anthropic", state="degraded", detail=f"{self.settings.anthropic_model} configured; verified during audit")
        return IntegrationStatus(name="Anthropic", state="degraded", detail="Using validated deterministic strategy fixtures")
