from app.models.schemas import (
    EmployeeReply,
    EvaluationScores,
    Leak,
    Metrics,
    RedundancyEvent,
    SpendRecord,
    Strategy,
)

METRICS = Metrics()

SPEND = [
    SpendRecord(vendor="Slack", annual_spend=52_800, active_seats=89, purchased_seats=220, status="leaking"),
    SpendRecord(vendor="Datadog", annual_spend=118_000, status="leaking"),
    SpendRecord(vendor="Figma", annual_spend=7_200, active_seats=0, purchased_seats=12, status="zombie"),
    SpendRecord(vendor="Notion", annual_spend=18_000, active_seats=412, purchased_seats=450, status="healthy"),
    SpendRecord(vendor="Zoom", annual_spend=14_400, active_seats=167, purchased_seats=240, status="review"),
    SpendRecord(vendor="Miro", annual_spend=9_600, active_seats=41, purchased_seats=80, status="review"),
    SpendRecord(vendor="GitHub", annual_spend=54_000, active_seats=173, purchased_seats=180, status="healthy"),
    SpendRecord(vendor="Jira", annual_spend=39_600, active_seats=301, purchased_seats=330, status="healthy"),
    SpendRecord(vendor="Confluence", annual_spend=22_800, active_seats=198, purchased_seats=330, status="review"),
    SpendRecord(vendor="Asana", annual_spend=12_000, active_seats=17, purchased_seats=100, status="review"),
    SpendRecord(vendor="Loom", annual_spend=8_400, active_seats=63, purchased_seats=140, status="review"),
    SpendRecord(vendor="1Password", annual_spend=15_600, active_seats=252, purchased_seats=260, status="healthy"),
]

LEAKS = [
    Leak(id="slack-unused", vendor="Slack", leak_type="Unused licenses", annual_loss=31_440, severity="critical", evidence="131 of 220 paid seats are inactive."),
    Leak(id="slack-negotiation", vendor="Slack", leak_type="Negotiation leak", annual_loss=13_200, severity="high", evidence="$20 seat price exceeds the $15 benchmark."),
    Leak(id="datadog-overbilling", vendor="Datadog", leak_type="Overbilling", annual_loss=18_000, severity="high", evidence="Annual spend exceeds contracted amount by $18,000."),
    Leak(id="datadog-switch", vendor="Datadog", leak_type="Switching opportunity", annual_loss=42_000, severity="high", evidence="Grafana benchmark is $42,000 below current annual spend."),
    Leak(id="figma-zombie", vendor="Figma", leak_type="Zombie subscription", annual_loss=7_200, severity="high", evidence="No recorded usage in the last 60 days."),
]

REDUNDANCY = [
    RedundancyEvent(tool_a="Datadog", tool_b="Grafana", overlap_score=0.86, annual_redundant_spend=24_000, rationale="Monitoring, dashboards, alerting, and log-analysis capabilities overlap."),
]

EMPLOYEE_REPLIES = [
    EmployeeReply(employee="Sarah Chen", days_active_90d=0, manager="Maya Patel", reply="3", response="I no longer need Slack. Please reclaim the seat.", interpretation="reclaim", recoverable=240),
    EmployeeReply(employee="John Miller", days_active_90d=71, manager="Maya Patel", reply="1", response="I use Slack every day. Please keep it.", interpretation="keep", recoverable=0),
    EmployeeReply(employee="Alex Rivera", days_active_90d=9, manager="Jordan Lee", reply="2", response="I only need messaging. A lower tier is fine.", interpretation="downgrade", recoverable=96),
    EmployeeReply(employee="Priya Shah", days_active_90d=0, manager="Jordan Lee", reply="3", response="This seat is no longer needed. Please reclaim it.", interpretation="reclaim", recoverable=240),
    EmployeeReply(employee="Elena Rossi", vendor="Figma", resource="Morgan Liu / Professional seat", days_active_90d=0, manager="Design", reply="3", response="Morgan has departed. Remove the unused Figma seat.", interpretation="reclaim", recoverable=600),
]

RESEARCH_TARGETS = [
    {"vendor": "Slack", "competitor": "Microsoft Teams", "benchmark": 15.0, "url": "https://slack.com/pricing", "query": "Slack enterprise pricing per user official", "finding": "Current seat price is 33% above the verified market benchmark.", "category": "Current vendor"},
    {"vendor": "Microsoft Teams", "competitor": "Slack", "benchmark": 12.5, "url": "https://www.microsoft.com/en-us/microsoft-teams/compare-microsoft-teams-options", "query": "Microsoft Teams business pricing official", "finding": "A bundled collaboration alternative strengthens Slack negotiation leverage.", "category": "Competitor"},
    {"vendor": "Datadog", "competitor": "Grafana Cloud", "benchmark": 100_000.0, "url": "https://www.datadoghq.com/pricing/", "query": "Datadog infrastructure monitoring pricing official", "finding": "Contracted annual baseline confirms an $18,000 overbilling delta.", "category": "Current vendor"},
    {"vendor": "Grafana", "competitor": "Datadog", "benchmark": 76_000.0, "url": "https://grafana.com/pricing/", "query": "Grafana Cloud pricing official", "finding": "Comparable monitoring coverage indicates a $42,000 switching opportunity.", "category": "Competitor"},
    {"vendor": "New Relic", "competitor": "Datadog", "benchmark": 82_000.0, "url": "https://newrelic.com/pricing", "query": "New Relic pricing official", "finding": "A second observability benchmark validates competitive pressure.", "category": "Competitor"},
    {"vendor": "Figma", "competitor": "Penpot", "benchmark": 600.0, "url": "https://www.figma.com/pricing/", "query": "Figma professional pricing official", "finding": "Official pricing supports the full $7,200 zombie-subscription recovery.", "category": "Current vendor"},
    {"vendor": "Notion", "competitor": "Confluence", "benchmark": 10.0, "url": "https://www.notion.com/pricing", "query": "Notion business pricing official", "finding": "Notion pricing anchors the knowledge-management redundancy review.", "category": "Current vendor"},
    {"vendor": "Confluence", "competitor": "Notion", "benchmark": 8.6, "url": "https://www.atlassian.com/software/confluence/pricing", "query": "Confluence pricing official", "finding": "Confluence provides a second knowledge-management cost benchmark.", "category": "Competitor"},
]

STRATEGIES = [
    Strategy(
        id="slack-cancel",
        vendor="Slack",
        title="Bulk-cancel all 131 inactive seats",
        description="Maximize savings by removing every inactive seat before checking whether occasional users still need access.",
        savings=31_440,
        risk="High",
        scores=EvaluationScores(confidence=0.91, action_safety=0.72, evidence_completeness=0.92, expected_roi=0.98, hallucination_risk=0.04, citation_coverage=1.0),
    ),
    Strategy(
        id="slack-downgrade",
        vendor="Slack",
        title="Recover only owner-verified Slack seats",
        description="Reclaim 84 confirmed no-use seats, downgrade 47 confirmed low-use seats, and protect 89 active users.",
        savings=22_400,
        risk="Low",
        scores=EvaluationScores(confidence=0.98, action_safety=0.96, evidence_completeness=1.0, expected_roi=0.91, hallucination_risk=0.02, citation_coverage=1.0),
    ),
    Strategy(
        id="slack-renegotiate",
        vendor="Slack",
        title="Renegotiate seat pricing",
        description="Use the verified market benchmark to request a revised enterprise rate.",
        savings=13_200,
        risk="Very Low",
        scores=EvaluationScores(confidence=0.88, action_safety=0.97, evidence_completeness=0.93, expected_roi=0.78, hallucination_risk=0.04, citation_coverage=1.0),
    ),
    Strategy(
        id="datadog-renegotiate",
        vendor="Datadog",
        title="Open Datadog contract review",
        description="Create an evidence-backed renegotiation draft covering overbilling and benchmark alternatives.",
        savings=18_000,
        risk="Very Low",
        scores=EvaluationScores(confidence=0.96, action_safety=0.98, evidence_completeness=0.97, expected_roi=0.88, hallucination_risk=0.02, citation_coverage=1.0),
    ),
    Strategy(
        id="figma-renewal-stop",
        vendor="Figma",
        title="Stop the unused Figma workspace renewal",
        description="Send formal non-renewal notice after zero usage and the design manager's removal confirmation.",
        savings=7_200,
        risk="Very Low",
        scores=EvaluationScores(confidence=0.98, action_safety=0.99, evidence_completeness=0.97, expected_roi=0.94, hallucination_risk=0.01, citation_coverage=1.0),
    ),
]
