from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationStatus(BaseModel):
    name: str
    state: Literal["connected", "degraded", "unavailable"]
    detail: str


class AuditEvent(BaseModel):
    step: str
    status: Literal["started", "progress", "completed", "warning", "failed"]
    message: str
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: int = 0
    payload: dict[str, Any] | None = None


class Metrics(BaseModel):
    potential_leakage: int = 111_840
    verified_recoverable: int = 82_300
    redundancy_savings: int = 24_000
    negotiation_leverage: int = 92
    action_priority: str = "CRITICAL"


class SpendRecord(BaseModel):
    vendor: str
    annual_spend: int
    active_seats: int | None = None
    purchased_seats: int | None = None
    status: str


class UploadedDocument(BaseModel):
    id: str
    name: str
    document_type: str
    size_bytes: int
    row_count: int
    status: Literal["parsed", "fixture", "unsupported"]
    summary: str
    evidence_count: int = 0


class EvidenceRecord(BaseModel):
    id: str
    document_id: str
    vendor: str
    claim: str
    locator: str
    value: str
    confidence: float


class DatasetSummary(BaseModel):
    documents: int = 0
    records: int = 0
    vendors: int = 0
    employees: int = 0
    contracts: int = 0
    invoices: int = 0
    capabilities: int = 0
    period: str = "FY2026"
    coverage: float = 0.0


class Leak(BaseModel):
    id: str
    vendor: str
    leak_type: str
    annual_loss: int
    severity: Literal["critical", "high", "medium", "low"]
    evidence: str


class RedundancyEvent(BaseModel):
    tool_a: str
    tool_b: str
    overlap_score: float
    annual_redundant_spend: int
    rationale: str


class EmployeeReply(BaseModel):
    employee: str
    vendor: str = "Slack"
    resource: str = "Pro license"
    days_active_90d: int = 0
    manager: str = ""
    reply: Literal["1", "2", "3"]
    response: str
    interpretation: Literal["keep", "downgrade", "reclaim"]
    recoverable: int


class TaskVerification(BaseModel):
    status: Literal["awaiting_reply", "confirmed_reclaim", "confirmed_keep", "unrecognized", "error"] = "awaiting_reply"
    channel_id: str = ""
    thread_ts: str | None = None
    posted_receipt_id: str | None = None
    prompt: str = ""
    response_text: str = ""
    interpretation: Literal["reclaim", "keep"] | None = None
    posted_at: datetime | None = None
    checked_at: datetime | None = None
    responded_at: datetime | None = None
    error_detail: str = ""


class VerificationEvent(BaseModel):
    id: str
    task_id: str
    vendor: str
    resource: str
    status: str
    response_text: str = ""
    interpretation: Literal["reclaim", "keep"] | None = None
    thread_ts: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now)


class ResearchFinding(BaseModel):
    vendor: str
    benchmark_price: float
    source_url: str
    source_status: Literal["live", "cached"]
    finding: str
    competitor: str = ""
    category: str = "Official pricing"
    search_query: str = ""
    page_title: str = ""
    evidence_excerpt: str = ""
    scraped_at: datetime = Field(default_factory=utc_now)


class ResearchActivity(BaseModel):
    id: str
    kind: Literal["search", "navigate", "inspect", "extract", "compare", "cite"]
    status: Literal["running", "completed", "cached"]
    label: str
    detail: str
    vendor: str = ""
    query: str = ""
    url: str = ""
    timestamp: datetime = Field(default_factory=utc_now)


class EvaluationScores(BaseModel):
    confidence: float
    action_safety: float
    evidence_completeness: float
    expected_roi: float
    hallucination_risk: float
    citation_coverage: float


class Strategy(BaseModel):
    id: str
    vendor: str
    title: str
    description: str
    savings: int
    risk: str
    scores: EvaluationScores
    approved: bool = False
    gate_result: Literal["execute", "human_review"] = "human_review"


class ActionReceipt(BaseModel):
    id: str
    kind: str
    title: str
    status: Literal["executed", "simulated", "failed", "blocked"]
    tool: str
    resource_id: str | None = None
    detail: str
    payload: dict[str, Any] | None = None


class RecoveryTask(BaseModel):
    id: str
    strategy_id: str
    vendor: str
    title: str
    action: str
    savings: int
    owner: str = "Project Head"
    urgency: Literal["now", "this_week", "before_renewal"]
    status: Literal["awaiting_verification", "pending_approval", "approved", "held", "rejected", "executed", "failed", "closed_no_action"] = "pending_approval"
    recommendation: Literal["approve", "review", "hold"]
    gate_confidence: float
    gate_action_safety: float
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    draft_to: str
    draft_subject: str
    draft_body: str
    decision_note: str = ""
    decided_at: datetime | None = None
    receipts: list[str] = Field(default_factory=list)
    verification: TaskVerification | None = None


class TaskDecisionRequest(BaseModel):
    decision: Literal["approve", "hold", "reject"]
    note: str = ""


class TraceNode(BaseModel):
    id: str
    label: str
    status: Literal["pending", "running", "completed", "warning"]
    duration_ms: int = 0
    children: list["TraceNode"] = Field(default_factory=list)


class ClickHouseAnalytics(BaseModel):
    source: Literal["clickhouse", "fixture"] = "fixture"
    row_count: int = 0
    freshness: str = "waiting"
    spend_by_vendor: list[dict[str, Any]] = Field(default_factory=list)
    leakage_by_category: list[dict[str, Any]] = Field(default_factory=list)
    recovery_pipeline: list[dict[str, Any]] = Field(default_factory=list)
    table_counts: list[dict[str, Any]] = Field(default_factory=list)
    query_log: list[dict[str, Any]] = Field(default_factory=list)


class AuditSnapshot(BaseModel):
    audit_id: UUID
    company: str = "AcmeAI"
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    integrations: list[IntegrationStatus] = Field(default_factory=list)
    metrics: Metrics = Field(default_factory=Metrics)
    uploaded_documents: list[UploadedDocument] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    dataset_summary: DatasetSummary = Field(default_factory=DatasetSummary)
    spend: list[SpendRecord] = Field(default_factory=list)
    leaks: list[Leak] = Field(default_factory=list)
    redundancy: list[RedundancyEvent] = Field(default_factory=list)
    employee_replies: list[EmployeeReply] = Field(default_factory=list)
    verification_events: list[VerificationEvent] = Field(default_factory=list)
    research: list[ResearchFinding] = Field(default_factory=list)
    research_activity: list[ResearchActivity] = Field(default_factory=list)
    strategies: list[Strategy] = Field(default_factory=list)
    recovery_tasks: list[RecoveryTask] = Field(default_factory=list)
    actions: list[ActionReceipt] = Field(default_factory=list)
    trace_tree: TraceNode | None = None
    trace_id: str | None = None
    trace_url: str | None = None
    analytics: ClickHouseAnalytics = Field(default_factory=ClickHouseAnalytics)
    report_markdown: str = ""


class AuditCreated(BaseModel):
    audit_id: UUID
    status: str
    events_url: str
