import asyncio
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.models.schemas import AuditEvent, AuditSnapshot, DatasetSummary, EvidenceRecord, UploadedDocument


@dataclass
class AuditRun:
    snapshot: AuditSnapshot
    events: list[AuditEvent] = field(default_factory=list)
    subscribers: set[asyncio.Queue] = field(default_factory=set)

    async def publish(self, event: AuditEvent) -> None:
        self.events.append(event)
        for queue in list(self.subscribers):
            await queue.put(event)


class AuditRunStore:
    def __init__(self) -> None:
        self._runs: dict[UUID, AuditRun] = {}

    def create(
        self,
        documents: list[UploadedDocument] | None = None,
        evidence: list[EvidenceRecord] | None = None,
        dataset_summary: DatasetSummary | None = None,
    ) -> AuditRun:
        if documents is None:
            from app.services.data_room import ingest_data_room

            ingestion = ingest_data_room()
            documents = ingestion.documents
            evidence = ingestion.evidence
            dataset_summary = ingestion.summary
        audit_id = uuid4()
        run = AuditRun(
            snapshot=AuditSnapshot(
                audit_id=audit_id,
                uploaded_documents=documents or [],
                evidence=evidence or [],
                dataset_summary=dataset_summary or DatasetSummary(),
            )
        )
        self._runs[audit_id] = run
        return run

    def get(self, audit_id: UUID) -> AuditRun | None:
        return self._runs.get(audit_id)


store = AuditRunStore()
