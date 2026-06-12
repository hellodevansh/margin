# Margin

Margin is a local autonomous SaaS spend recovery demo. It turns contracts, usage, invoices, and live market data into evidence-backed actions a project head can approve with confidence.

## Demo workflow

The landing page begins with an empty audit data room. Nothing is prefilled in the UI, and the audit remains locked until the user selects all seven canonical demo files from `backend/app/fixtures/data_room`:

- Spend ledger: 12-vendor software estate and ownership.
- License usage: employee-level activity and reclaim/downgrade candidates.
- Verified license cohorts: 84 Slack reclaims, 47 downgrades, and 89 protected active seats.
- Contract register: commitments, renewal windows, pricing, and auto-renew terms.
- Invoice ledger: contract-to-invoice variance evidence.
- Capability matrix: normalized overlap for redundancy detection.
- Employee roster: employment and manager context for safe verification.

Users can add CSV, JSON, PDF, Word, Markdown, or text evidence before starting. The judge-facing narrative is:

1. **Detect**: find potential recoverable spend.
2. **Verify**: ask resource owners before acting.
3. **Research**: build the market case visibly in the browser.
4. **Gate**: use Langfuse-audited scores to block unsafe strategies.
5. **Decide**: present only gate-released actions to the project head.
6. **Recover**: create the approved vendor-facing draft and retain the receipt.

The Slack story makes the gate causally necessary. Margin blocks a tempting `$31,440` bulk cancellation because action safety is `0.72`, then releases the owner-verified `$22,400` reclaim-and-downgrade action at `0.96` safety and `0.98` confidence. Recovery tasks are generated only from passed strategies.

Slack never carries project-head decisions. Approving a task inside Margin creates a live, actionable Outlook draft addressed to the relevant vendor. Drafts request concrete remedies, terms, credits, confirmations, and deadlines; they are never sent automatically. Holding or rejecting a task stays inside Margin and launches no external work.

The backend rejects empty or incomplete submissions. Uploaded canonical filenames retain their evidence lineage, so the complete uploaded demo package covers every workflow while still making document ingestion visible to judges.

During market research, the live audit exposes the browser agent's current search query, official URL, extraction activity, competitor comparison, and live/cached source state. The complete uploaded package covers eight official pricing sources and produces 33 observable browser operations.

ClickHouse persists the complete evidence-to-execution trail throughout the workflow. Langfuse is the audited decision gate; ClickHouse is the durable analytical memory.

## Local setup

```bash
cp backend/.env.example backend/.env
cd backend && uv sync --extra dev
cd ../frontend && npm install
cd ..
chmod +x scripts/dev.sh
./scripts/dev.sh
```

Open [http://localhost:3000](http://localhost:3000). The API runs at [http://localhost:8000](http://localhost:8000).

The full demo works without credentials using deterministic fixtures and simulated action receipts. Add credentials to `backend/.env` to enable real Langfuse, ClickHouse, Anthropic, and Composio integrations.

## Credential setup

- Langfuse: project public key, secret key, cloud base URL, and the project URL used for trace deep links.
- ClickHouse Cloud: HTTPS hostname, port `8443`, database, username, and password.
- Composio: API key and the `margin` user with Slack and Outlook connected through Composio-managed OAuth.
- Action destination: a Slack resource-verification channel. Approved Outlook drafts use the relevant vendor contact embedded in each recovery task.
- Anthropic: API key with access to `claude-sonnet-4-6`.

Leave `DEMO_ACTIONS_ENABLED=false` until the connected demo accounts and action destinations have been verified. The preflight command performs read-only credential checks.

### ClickHouse Cloud

This project uses ClickHouse Cloud directly and does not require Docker. Create a service in the ClickHouse Cloud console, open **Connect**, select **HTTPS**, and place the connection values in `backend/.env`:

```dotenv
CLICKHOUSE_HOST=<service-hostname-without-https>
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<service-password>
CLICKHOUSE_DATABASE=default
CLICKHOUSE_SECURE=true
```

The first completed audit creates the required `MergeTree` tables and writes the demo's analytical memory. Keep `CLICKHOUSE_HOST` and `CLICKHOUSE_PASSWORD` blank to use fixture analytics while the Cloud service is not configured.

## Preflight and tests

```bash
uv run --project backend python scripts/preflight.py
cd backend && uv run pytest
cd frontend && npm run lint && npm run build
```
# margin
