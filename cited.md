# Margin Spend Recovery Report

## Executive Summary

Margin audited AcmeAI's SaaS estate and identified **$111,840** in potential leakage. The system then verified the evidence, researched the market, and used the Langfuse decision gate to release only safe recovery actions.

## Metrics

- Potential Leakage: $111,840
- Verified Recoverable: $82,300
- Redundancy Savings: $24,000
- Negotiation Leverage: 92/100

## Data Room

Margin normalized **7 documents**, **60 source records**, and **12 vendors** with **96% evidence coverage**.

| Document | Type | Records | Evidence Links |
| --- | --- | ---: | ---: |
| spend_ledger.csv | Spend ledger | 12 | 1 |
| license_usage_90d.csv | Usage export | 8 | 1 |
| license_decision_cohorts.csv | Verified license cohorts | 4 | 1 |
| contracts.json | Contract register | 6 | 3 |
| invoices_q2.csv | Invoice ledger | 8 | 1 |
| capability_matrix.csv | Capability matrix | 14 | 1 |
| employee_roster.csv | Employee roster | 8 | 1 |

## Evidence Lineage

| Vendor | Claim | Source Locator | Confidence |
| --- | --- | --- | ---: |
| Slack | 131 paid seats are inactive | `spend_ledger.csv / Slack / seats` | 99% |
| Slack | Owner verification separates inactive seats into safe recovery cohorts | `license_decision_cohorts.csv / Slack cohorts` | 99% |
| Slack | Current unit price is $20 per user/month | `contracts.json / CTR-SLK-2026` | 100% |
| Datadog | Annual committed baseline is $100,000 | `contracts.json / CTR-DD-2026` | 100% |
| Datadog | Four invoices exceed contract baseline by $4,500 each | `invoices_q2.csv / INV-10421..INV-11602` | 99% |
| Datadog | Datadog and Grafana overlap across monitoring, dashboards, alerting, and logs | `capability_matrix.csv / Datadog + Grafana` | 94% |
| Figma | Professional workspace has no activity in the review window | `license_usage_90d.csv / Morgan Liu` | 98% |
| Figma | Figma renews within the action window | `contracts.json / CTR-FIG-2026` | 100% |
| Slack | License decisions are cross-checked against employment status and managers | `employee_roster.csv / all rows` | 96% |

## Leak Table

| Vendor | Leak Type | Annual Loss | Severity |
| --- | --- | ---: | --- |
| Slack | Unused licenses | $31,440 | Critical |
| Slack | Negotiation leak | $13,200 | High |
| Datadog | Overbilling | $18,000 | High |
| Datadog | Switching opportunity | $42,000 | High |
| Figma | Zombie subscription | $7,200 | High |

## Redundancy Analysis

Datadog and Grafana have an overlap score of **0.86**, representing **$24,000** in redundant annual spend.

## Strategies Evaluated

| Strategy | Savings | Safety | Confidence | Gate |
| --- | ---: | ---: | ---: | --- |
| Bulk-cancel all 131 inactive seats | $31,440 | 0.72 | 0.91 | Human Review |
| Recover only owner-verified Slack seats | $22,400 | 0.96 | 0.98 | Execute |
| Renegotiate seat pricing | $13,200 | 0.97 | 0.88 | Human Review |
| Open Datadog contract review | $18,000 | 0.98 | 0.96 | Execute |
| Stop the unused Figma workspace renewal | $7,200 | 0.99 | 0.98 | Execute |

## Deterministic Resource Confirmations

These prepared confirmations keep the broader demo dataset deterministic.

| Resource Owner | Resource | Active Days (90d) | Confirmation | Interpreted Result |
| --- | --- | ---: | --- | --- |
| Sarah Chen | Slack / Pro license | 0 | I no longer need Slack. Please reclaim the seat. | Reclaim |
| John Miller | Slack / Pro license | 71 | I use Slack every day. Please keep it. | Keep |
| Alex Rivera | Slack / Pro license | 9 | I only need messaging. A lower tier is fine. | Downgrade |
| Priya Shah | Slack / Pro license | 0 | This seat is no longer needed. Please reclaim it. | Reclaim |

## Live Slack-Gated Verification

The Figma recovery item remains locked until Margin reads `RECLAIM` from the live Slack thread. A `KEEP` reply closes the item with no vendor action. Final project-head decisions are recorded only inside Margin.

| Vendor | Resource | Verification Status | Live Response |
| --- | --- | --- | --- |
| Figma | Morgan Liu / Professional workspace | Posted | Waiting for Slack thread reply |

## External Action Receipts

- **Figma owner confirmation requested**: executed via `SLACK_CHAT_POST_MESSAGE`

## Gate-Released Decision Queue

Only strategies that pass the Langfuse-audited safety and confidence policy can enter this queue. Approve, Hold, and Reject decisions happen only inside Margin.

| Vendor | Strategy ID | Task | Annual Recovery | Safety | Confidence | Status |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Figma | `figma-renewal-stop` | Stop the unused Figma renewal | $7,200 | 0.99 | 0.98 | Awaiting Verification |
| Datadog | `datadog-renegotiate` | Recover the Datadog billing variance | $18,000 | 0.98 | 0.96 | Pending Approval |
| Slack | `slack-downgrade` | Recover owner-verified Slack seats | $22,400 | 0.96 | 0.98 | Pending Approval |

## Vendor Drafts Prepared

Approving a task creates the corresponding actionable vendor-facing Outlook draft. Drafts are never sent automatically.

| Vendor | Recipient | Subject |
| --- | --- | --- |
| Figma | support@figma.com | Formal Figma non-renewal notice for AcmeAI Professional workspace |
| Datadog | billing@datadoghq.com | Request for $18,000 credit and revised Datadog order form |
| Slack | renewals@slack.com | Slack renewal true-down request for AcmeAI |

## Langfuse Decision Gate

Langfuse records the Claude generation, browser-research context, six scores per strategy, and the deterministic gate result. Recovery tasks are generated only from strategies with action safety of at least **0.85** and confidence of at least **0.90**. Blocked strategies cannot enter the project-head queue.

## ClickHouse Analytical Memory

ClickHouse persists and queries back **86 rows** across **12 analytical tables** for this audit run.

## Source URLs

- [Slack pricing](https://slack.com/pricing) - live - compared with Microsoft Teams - Current seat price is 33% above the verified market benchmark.
- [Microsoft Teams pricing](https://www.microsoft.com/en-us/microsoft-teams/compare-microsoft-teams-options) - live - compared with Slack - A bundled collaboration alternative strengthens Slack negotiation leverage.
- [Datadog pricing](https://www.datadoghq.com/pricing/) - live - compared with Grafana Cloud - Contracted annual baseline confirms an $18,000 overbilling delta.
- [Grafana pricing](https://grafana.com/pricing/) - live - compared with Datadog - Comparable monitoring coverage indicates a $42,000 switching opportunity.
- [New Relic pricing](https://newrelic.com/pricing) - live - compared with Datadog - A second observability benchmark validates competitive pressure.
- [Figma pricing](https://www.figma.com/pricing/) - live - compared with Penpot - Official pricing supports the full $7,200 zombie-subscription recovery.
- [Notion pricing](https://www.notion.com/pricing) - live - compared with Confluence - Notion pricing anchors the knowledge-management redundancy review.
- [Confluence pricing](https://www.atlassian.com/software/confluence/pricing) - live - compared with Notion - Confluence provides a second knowledge-management cost benchmark.
