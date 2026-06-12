from copy import deepcopy

from app.fixtures.demo_data import EMPLOYEE_REPLIES, LEAKS, METRICS, RESEARCH_TARGETS, STRATEGIES
from app.integrations.composio_client import ComposioAdapter, interpret_verification_reply, latest_human_thread_reply
from app.integrations.clickhouse_client import fixture_analytics
from app.models.schemas import AuditSnapshot, ResearchFinding
from app.services.report import build_report
from app.settings import Settings
from app.services.tasks import build_recovery_tasks


def test_slack_is_only_used_for_resource_verification():
    adapter = ComposioAdapter(
        Settings(
            _env_file=None,
            composio_api_key="",
            demo_actions_enabled=False,
        )
    )
    action, verification = adapter.request_figma_verification("audit-id")
    assert action.status == "simulated"
    assert action.tool == "SLACK_CHAT_POST_MESSAGE"
    assert action.kind == "Slack usage verification"
    assert "Final approval and vendor action happen inside Margin" in action.payload["markdown_text"]
    assert "RECLAIM" in action.payload["markdown_text"]
    assert verification.status == "error"


def test_slack_reply_interpretation_is_strict_and_case_insensitive():
    assert interpret_verification_reply("reclaim") == "reclaim"
    assert interpret_verification_reply("KEEP") == "keep"
    assert interpret_verification_reply("please reclaim") == "reclaim"
    assert interpret_verification_reply("KEEP or RECLAIM") is None
    assert interpret_verification_reply("approved") is None


def test_latest_human_thread_reply_ignores_parent_and_bot_messages():
    result = {
        "data": {
            "messages": [
                {"ts": "100.000", "text": "Parent prompt", "bot_id": "B1"},
                {"ts": "101.000", "text": "KEEP", "bot_id": "B2"},
                {"ts": "102.000", "text": "RECLAIM", "user": "U1"},
            ]
        }
    }
    assert latest_human_thread_reply(result, "100.000") == "RECLAIM"


def test_approved_task_uses_outlook_only():
    adapter = ComposioAdapter(
        Settings(
            _env_file=None,
            composio_api_key="",
            demo_actions_enabled=False,
            slack_finance_channel_id="C123",
        )
    )
    actions = adapter.execute_task_decision(build_recovery_tasks()[1], "approve", "Proceed")
    assert len(actions) == 1
    outlook = actions[0]
    assert outlook.kind == "Vendor negotiation draft"
    assert outlook.tool == "OUTLOOK_CREATE_DRAFT"
    assert outlook.payload["to_recipients"] == ["billing@datadoghq.com"]
    assert outlook.payload["subject"] == "Request for $18,000 credit and revised Datadog order form"
    assert "credit memo for the $18,000 overbilling variance" in outlook.payload["body"]
    assert "within five business days" in outlook.payload["body"]
    assert "project head approved" not in outlook.payload["body"].lower()
    assert "begin the required follow-up" not in outlook.payload["body"].lower()


def test_hold_decision_stays_inside_margin():
    adapter = ComposioAdapter(Settings(_env_file=None, composio_api_key="", demo_actions_enabled=False))
    actions = adapter.execute_task_decision(build_recovery_tasks()[0], "hold", "Review next week")
    assert actions == []


def test_every_recovery_task_has_an_actionable_vendor_draft():
    tasks = build_recovery_tasks()
    assert {task.draft_to for task in tasks} == {"renewals@slack.com", "billing@datadoghq.com", "support@figma.com"}
    assert all(task.vendor.lower() in task.draft_subject.lower() for task in tasks)
    assert all("Please" in task.draft_body for task in tasks)
    assert all("Regards," in task.draft_body for task in tasks)
    assert all("project head approved" not in task.draft_body.lower() for task in tasks)


def test_clickhouse_memory_exposes_tables_and_queries():
    snapshot = AuditSnapshot(audit_id="11111111-1111-1111-1111-111111111111")
    snapshot.recovery_tasks = build_recovery_tasks()
    analytics = fixture_analytics(snapshot)
    assert analytics.table_counts
    assert "verification_events" in {item["table"] for item in analytics.table_counts}
    assert analytics.query_log
    assert {query["name"] for query in analytics.query_log} == {"Vendor spend", "Leakage by category", "Strategy gate memory"}


def test_report_contains_every_market_source():
    snapshot = AuditSnapshot(audit_id="11111111-1111-1111-1111-111111111111")
    snapshot.metrics = deepcopy(METRICS)
    snapshot.leaks = deepcopy(LEAKS)
    snapshot.strategies = deepcopy(STRATEGIES)
    snapshot.employee_replies = deepcopy(EMPLOYEE_REPLIES)
    snapshot.research = [
        ResearchFinding(vendor=target["vendor"], benchmark_price=target["benchmark"], source_url=target["url"], source_status="cached", finding=target["finding"])
        for target in RESEARCH_TARGETS
    ]
    report = build_report(snapshot)
    assert "$111,840" in report
    assert "Final project-head decisions are recorded only inside Margin" in report
    assert all(target["url"] in report for target in RESEARCH_TARGETS)
