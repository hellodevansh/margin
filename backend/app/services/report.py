from app.models.schemas import AuditSnapshot


def build_report(snapshot: AuditSnapshot) -> str:
    documents = "\n".join(f"| {x.name} | {x.document_type} | {x.row_count} | {x.evidence_count} |" for x in snapshot.uploaded_documents)
    evidence_rows = "\n".join(f"| {x.vendor} | {x.claim} | `{x.locator}` | {x.confidence:.0%} |" for x in snapshot.evidence)
    leak_rows = "\n".join(f"| {x.vendor} | {x.leak_type} | ${x.annual_loss:,.0f} | {x.severity.title()} |" for x in snapshot.leaks)
    sources = "\n".join(f"- [{x.vendor} pricing]({x.source_url}) - {x.source_status} - compared with {x.competitor or 'contract baseline'} - {x.finding}" for x in snapshot.research)
    strategy_rows = "\n".join(f"| {x.title} | ${x.savings:,.0f} | {x.scores.action_safety:.2f} | {x.scores.confidence:.2f} | {x.gate_result.replace('_', ' ').title()} |" for x in snapshot.strategies)
    actions = "\n".join(f"- **{x.title}**: {x.status} via `{x.tool}`" for x in snapshot.actions)
    tasks = "\n".join(f"| {x.vendor} | `{x.strategy_id}` | {x.title} | ${x.savings:,.0f} | {x.gate_action_safety:.2f} | {x.gate_confidence:.2f} | {x.status.replace('_', ' ').title()} |" for x in snapshot.recovery_tasks)
    drafts = "\n".join(f"| {x.vendor} | {x.draft_to} | {x.draft_subject} |" for x in snapshot.recovery_tasks)
    verification_rows = "\n".join(f"| {x.employee} | {x.vendor} / {x.resource} | {x.days_active_90d} | {x.response} | {x.interpretation.title()} |" for x in snapshot.employee_replies)
    live_verification_rows = "\n".join(
        f"| {x.vendor} | {x.resource} | {x.status.replace('_', ' ').title()} | {x.response_text or 'Waiting for Slack thread reply'} |"
        for x in snapshot.verification_events
    )
    return f"""# Margin Spend Recovery Report

## Executive Summary

Margin audited AcmeAI's SaaS estate and identified **${snapshot.metrics.potential_leakage:,.0f}** in potential leakage. The system then verified the evidence, researched the market, and used the Langfuse decision gate to release only safe recovery actions.

## Metrics

- Potential Leakage: ${snapshot.metrics.potential_leakage:,.0f}
- Verified Recoverable: ${snapshot.metrics.verified_recoverable:,.0f}
- Redundancy Savings: ${snapshot.metrics.redundancy_savings:,.0f}
- Negotiation Leverage: {snapshot.metrics.negotiation_leverage}/100

## Data Room

Margin normalized **{snapshot.dataset_summary.documents} documents**, **{snapshot.dataset_summary.records} source records**, and **{snapshot.dataset_summary.vendors} vendors** with **{snapshot.dataset_summary.coverage:.0%} evidence coverage**.

| Document | Type | Records | Evidence Links |
| --- | --- | ---: | ---: |
{documents}

## Evidence Lineage

| Vendor | Claim | Source Locator | Confidence |
| --- | --- | --- | ---: |
{evidence_rows}

## Leak Table

| Vendor | Leak Type | Annual Loss | Severity |
| --- | --- | ---: | --- |
{leak_rows}

## Redundancy Analysis

Datadog and Grafana have an overlap score of **0.86**, representing **$24,000** in redundant annual spend.

## Strategies Evaluated

| Strategy | Savings | Safety | Confidence | Gate |
| --- | ---: | ---: | ---: | --- |
{strategy_rows}

## Deterministic Resource Confirmations

These prepared confirmations keep the broader demo dataset deterministic.

| Resource Owner | Resource | Active Days (90d) | Confirmation | Interpreted Result |
| --- | --- | ---: | --- | --- |
{verification_rows}

## Live Slack-Gated Verification

The Figma recovery item remains locked until Margin reads `RECLAIM` from the live Slack thread. A `KEEP` reply closes the item with no vendor action. Final project-head decisions are recorded only inside Margin.

| Vendor | Resource | Verification Status | Live Response |
| --- | --- | --- | --- |
{live_verification_rows}

## External Action Receipts

{actions}

## Gate-Released Decision Queue

Only strategies that pass the Langfuse-audited safety and confidence policy can enter this queue. Approve, Hold, and Reject decisions happen only inside Margin.

| Vendor | Strategy ID | Task | Annual Recovery | Safety | Confidence | Status |
| --- | --- | --- | ---: | ---: | ---: | --- |
{tasks}

## Vendor Drafts Prepared

Approving a task creates the corresponding actionable vendor-facing Outlook draft. Drafts are never sent automatically.

| Vendor | Recipient | Subject |
| --- | --- | --- |
{drafts}

## Langfuse Decision Gate

Langfuse records the Claude generation, browser-research context, six scores per strategy, and the deterministic gate result. Recovery tasks are generated only from strategies with action safety of at least **0.85** and confidence of at least **0.90**. Blocked strategies cannot enter the project-head queue.

## ClickHouse Analytical Memory

ClickHouse persists and queries back **{snapshot.analytics.row_count} rows** across **{len(snapshot.analytics.table_counts)} analytical tables** for this audit run.

## Source URLs

{sources}
"""
