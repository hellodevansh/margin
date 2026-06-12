from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import AuditSnapshot, ClickHouseAnalytics, IntegrationStatus
from app.settings import Settings


SCHEMA = [
    "CREATE TABLE IF NOT EXISTS audit_runs (audit_run_id UUID, company String, status LowCardinality(String), potential_leakage UInt64, verified_recoverable UInt64, created_at DateTime64(3)) ENGINE=MergeTree ORDER BY (created_at, audit_run_id)",
    "CREATE TABLE IF NOT EXISTS spend_history (audit_run_id UUID, vendor String, annual_spend UInt64, active_seats Nullable(UInt32), purchased_seats Nullable(UInt32), timestamp DateTime64(3)) ENGINE=MergeTree ORDER BY (vendor, timestamp)",
    "CREATE TABLE IF NOT EXISTS leak_events (audit_run_id UUID, vendor String, leak_type String, annual_loss UInt64, severity LowCardinality(String), detected_at DateTime64(3)) ENGINE=MergeTree ORDER BY (vendor, detected_at)",
    "CREATE TABLE IF NOT EXISTS market_benchmarks (audit_run_id UUID, vendor String, benchmark_price Float64, source_url String, source_status LowCardinality(String), scraped_at DateTime64(3)) ENGINE=MergeTree ORDER BY (vendor, scraped_at)",
    "CREATE TABLE IF NOT EXISTS redundancy_events (audit_run_id UUID, tool_a String, tool_b String, overlap_score Float64, annual_redundant_spend UInt64, detected_at DateTime64(3)) ENGINE=MergeTree ORDER BY (tool_a, detected_at)",
    "CREATE TABLE IF NOT EXISTS strategy_evaluations (audit_run_id UUID, strategy_id String, vendor String, savings UInt64, confidence Float64, action_safety Float64, expected_roi Float64, approved Bool, evaluated_at DateTime64(3)) ENGINE=MergeTree ORDER BY (vendor, evaluated_at)",
    "CREATE TABLE IF NOT EXISTS action_events (audit_run_id UUID, action_id String, kind String, status LowCardinality(String), tool String, resource_id Nullable(String), executed_at DateTime64(3)) ENGINE=MergeTree ORDER BY (kind, executed_at)",
    "CREATE TABLE IF NOT EXISTS source_documents (audit_run_id UUID, document_id String, name String, document_type String, row_count UInt32, status LowCardinality(String), ingested_at DateTime64(3)) ENGINE=MergeTree ORDER BY (document_type, ingested_at)",
    "CREATE TABLE IF NOT EXISTS evidence_records (audit_run_id UUID, evidence_id String, document_id String, vendor String, claim String, locator String, evidence_value String, confidence Float64, created_at DateTime64(3)) ENGINE=MergeTree ORDER BY (vendor, created_at)",
    "CREATE TABLE IF NOT EXISTS verification_events (audit_run_id UUID, event_id String, task_id String, vendor String, resource String, status LowCardinality(String), response_text String, interpretation Nullable(String), thread_ts Nullable(String), occurred_at DateTime64(3)) ENGINE=MergeTree ORDER BY (task_id, occurred_at)",
    "CREATE TABLE IF NOT EXISTS research_activity (audit_run_id UUID, activity_id String, kind LowCardinality(String), status LowCardinality(String), vendor String, query String, url String, detail String, occurred_at DateTime64(3)) ENGINE=MergeTree ORDER BY (kind, occurred_at)",
    "CREATE TABLE IF NOT EXISTS recovery_tasks (audit_run_id UUID, task_id String, vendor String, title String, savings UInt64, owner String, urgency LowCardinality(String), status LowCardinality(String), recommendation LowCardinality(String), decision_note String, updated_at DateTime64(3)) ENGINE=MergeTree ORDER BY (status, updated_at)",
]

TABLES = [
    "audit_runs",
    "spend_history",
    "leak_events",
    "market_benchmarks",
    "redundancy_events",
    "strategy_evaluations",
    "action_events",
    "source_documents",
    "evidence_records",
    "verification_events",
    "research_activity",
    "recovery_tasks",
]


class ClickHouseAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.clickhouse_host:
            try:
                import clickhouse_connect

                self.client = clickhouse_connect.get_client(
                    host=settings.clickhouse_host,
                    port=settings.clickhouse_port,
                    username=settings.clickhouse_user,
                    password=settings.clickhouse_password,
                    database=settings.clickhouse_database,
                    secure=settings.clickhouse_secure,
                    connect_timeout=5,
                )
            except Exception:
                self.client = None

    def status(self) -> IntegrationStatus:
        if self.client:
            return IntegrationStatus(name="ClickHouse", state="connected", detail="Cloud analytical memory enabled")
        return IntegrationStatus(name="ClickHouse", state="degraded", detail="Using fixture analytics; add ClickHouse credentials for persistence")

    def initialize(self) -> None:
        if self.client:
            for statement in SCHEMA:
                self.client.command(statement)

    def persist(self, snapshot: AuditSnapshot) -> ClickHouseAnalytics:
        if not self.client:
            return fixture_analytics(snapshot)
        try:
            self.initialize()
            run_id = str(snapshot.audit_id)
            now = datetime.now(timezone.utc)
            for table in TABLES:
                # Wait for each mutation before reinserting the audit snapshot so
                # an earlier asynchronous delete cannot remove the fresh rows.
                self.client.command(
                    f"ALTER TABLE {table} DELETE WHERE audit_run_id = {{run_id:UUID}} SETTINGS mutations_sync = 2",
                    parameters={"run_id": run_id},
                )
            self._insert("audit_runs", [[run_id, snapshot.company, snapshot.status, snapshot.metrics.potential_leakage, snapshot.metrics.verified_recoverable, now]])
            self._insert("spend_history", [[run_id, x.vendor, x.annual_spend, x.active_seats, x.purchased_seats, now] for x in snapshot.spend])
            self._insert("leak_events", [[run_id, x.vendor, x.leak_type, x.annual_loss, x.severity, now] for x in snapshot.leaks])
            self._insert("market_benchmarks", [[run_id, x.vendor, x.benchmark_price, x.source_url, x.source_status, x.scraped_at] for x in snapshot.research])
            self._insert("redundancy_events", [[run_id, x.tool_a, x.tool_b, x.overlap_score, x.annual_redundant_spend, now] for x in snapshot.redundancy])
            self._insert("strategy_evaluations", [[run_id, x.id, x.vendor, x.savings, x.scores.confidence, x.scores.action_safety, x.scores.expected_roi, x.approved, now] for x in snapshot.strategies])
            self._insert("action_events", [[run_id, x.id, x.kind, x.status, x.tool, x.resource_id, now] for x in snapshot.actions])
            self._insert("source_documents", [[run_id, x.id, x.name, x.document_type, x.row_count, x.status, now] for x in snapshot.uploaded_documents])
            self._insert("evidence_records", [[run_id, x.id, x.document_id, x.vendor, x.claim, x.locator, x.value, x.confidence, now] for x in snapshot.evidence])
            self._insert("verification_events", [[run_id, x.id, x.task_id, x.vendor, x.resource, x.status, x.response_text, x.interpretation, x.thread_ts, x.occurred_at] for x in snapshot.verification_events])
            self._insert("research_activity", [[run_id, x.id, x.kind, x.status, x.vendor, x.query, x.url, x.detail, x.timestamp] for x in snapshot.research_activity])
            self._insert("recovery_tasks", [[run_id, x.id, x.vendor, x.title, x.savings, x.owner, x.urgency, x.status, x.recommendation, x.decision_note, x.decided_at or now] for x in snapshot.recovery_tasks])
            return self._query_analytics(run_id, snapshot)
        except Exception:
            return fixture_analytics(snapshot)

    def _insert(self, table: str, rows: list[list[Any]]) -> None:
        if rows:
            # SharedMergeTree deduplicates identical insert blocks by default.
            # Re-persisting an audit after a human decision must restore all
            # unchanged evidence rows after the idempotent delete.
            self.client.insert(table, rows, settings={"insert_deduplicate": 0})

    def _query_analytics(self, run_id: str, snapshot: AuditSnapshot) -> ClickHouseAnalytics:
        parameters = {"run_id": run_id}
        spend_rows = self.client.query(
            "SELECT vendor, sum(annual_spend) FROM spend_history WHERE audit_run_id = {run_id:UUID} GROUP BY vendor ORDER BY sum(annual_spend) DESC",
            parameters=parameters,
        ).result_rows
        leakage_rows = self.client.query(
            "SELECT leak_type, sum(annual_loss) FROM leak_events WHERE audit_run_id = {run_id:UUID} GROUP BY leak_type ORDER BY sum(annual_loss) DESC",
            parameters=parameters,
        ).result_rows
        approved_rows = self.client.query(
            "SELECT sumIf(savings, approved) FROM strategy_evaluations WHERE audit_run_id = {run_id:UUID}",
            parameters=parameters,
        ).result_rows
        table_rows = self.client.query(
            """
            SELECT table_name, rows FROM (
              SELECT 'audit_runs' AS table_name, count() AS rows FROM audit_runs WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'spend_history', count() FROM spend_history WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'leak_events', count() FROM leak_events WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'market_benchmarks', count() FROM market_benchmarks WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'redundancy_events', count() FROM redundancy_events WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'strategy_evaluations', count() FROM strategy_evaluations WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'action_events', count() FROM action_events WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'source_documents', count() FROM source_documents WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'evidence_records', count() FROM evidence_records WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'verification_events', count() FROM verification_events WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'research_activity', count() FROM research_activity WHERE audit_run_id = {run_id:UUID}
              UNION ALL SELECT 'recovery_tasks', count() FROM recovery_tasks WHERE audit_run_id = {run_id:UUID}
            )
            ORDER BY table_name
            """,
            parameters=parameters,
        ).result_rows
        approved = int(approved_rows[0][0] or 0) if approved_rows else 0
        table_counts = [{"table": table, "rows": int(rows)} for table, rows in table_rows]
        return ClickHouseAnalytics(
            source="clickhouse",
            row_count=sum(item["rows"] for item in table_counts),
            freshness="live query",
            spend_by_vendor=[{"vendor": vendor, "spend": int(spend)} for vendor, spend in spend_rows],
            leakage_by_category=[{"category": category, "value": int(value)} for category, value in leakage_rows],
            recovery_pipeline=[
                {"stage": "Potential", "value": snapshot.metrics.potential_leakage},
                {"stage": "Verified", "value": snapshot.metrics.verified_recoverable},
                {"stage": "Gate released", "value": approved},
            ],
            table_counts=table_counts,
            query_log=query_log(run_id),
        )


def fixture_analytics(snapshot: AuditSnapshot) -> ClickHouseAnalytics:
    leakage = Counter()
    for leak in snapshot.leaks:
        leakage[leak.leak_type] += leak.annual_loss
    table_counts = snapshot_table_counts(snapshot)
    return ClickHouseAnalytics(
        source="fixture",
        row_count=sum(item["rows"] for item in table_counts),
        freshness="current audit",
        spend_by_vendor=[{"vendor": x.vendor, "spend": x.annual_spend} for x in snapshot.spend],
        leakage_by_category=[{"category": key, "value": value} for key, value in leakage.items()],
        recovery_pipeline=[
            {"stage": "Potential", "value": snapshot.metrics.potential_leakage},
            {"stage": "Verified", "value": snapshot.metrics.verified_recoverable},
            {"stage": "Gate released", "value": sum(x.savings for x in snapshot.strategies if x.approved)},
        ],
        table_counts=table_counts,
        query_log=query_log(str(snapshot.audit_id)),
    )


def snapshot_table_counts(snapshot: AuditSnapshot) -> list[dict[str, Any]]:
    return [
        {"table": "audit_runs", "rows": 1},
        {"table": "action_events", "rows": len(snapshot.actions)},
        {"table": "evidence_records", "rows": len(snapshot.evidence)},
        {"table": "leak_events", "rows": len(snapshot.leaks)},
        {"table": "market_benchmarks", "rows": len(snapshot.research)},
        {"table": "recovery_tasks", "rows": len(snapshot.recovery_tasks)},
        {"table": "redundancy_events", "rows": len(snapshot.redundancy)},
        {"table": "research_activity", "rows": len(snapshot.research_activity)},
        {"table": "source_documents", "rows": len(snapshot.uploaded_documents)},
        {"table": "spend_history", "rows": len(snapshot.spend)},
        {"table": "strategy_evaluations", "rows": len(snapshot.strategies)},
        {"table": "verification_events", "rows": len(snapshot.verification_events)},
    ]


def query_log(run_id: str) -> list[dict[str, Any]]:
    return [
        {
            "name": "Vendor spend",
            "purpose": "Rank the software estate by annual spend.",
            "sql": f"SELECT vendor, sum(annual_spend) FROM spend_history WHERE audit_run_id = '{run_id}' GROUP BY vendor ORDER BY sum(annual_spend) DESC",
        },
        {
            "name": "Leakage by category",
            "purpose": "Explain where recoverable spend is concentrated.",
            "sql": f"SELECT leak_type, sum(annual_loss) FROM leak_events WHERE audit_run_id = '{run_id}' GROUP BY leak_type ORDER BY sum(annual_loss) DESC",
        },
        {
            "name": "Strategy gate memory",
            "purpose": "Query the savings value released by the Langfuse-audited strategy gate.",
            "sql": f"SELECT sumIf(savings, approved) FROM strategy_evaluations WHERE audit_run_id = '{run_id}'",
        },
    ]
