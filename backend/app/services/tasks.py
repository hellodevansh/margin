from copy import deepcopy

from app.models.schemas import RecoveryTask, Strategy, TaskVerification


TASK_BLUEPRINTS = {
    "slack-downgrade": {
        "id": "slack-seat-recovery",
        "title": "Recover owner-verified Slack seats",
        "action": "Reclaim 84 confirmed no-use seats and downgrade 47 confirmed low-use seats.",
        "urgency": "now",
        "rationale": "Slack owner verification transformed a risky bulk-cancellation idea into a precise, reversible recovery action.",
        "evidence_refs": ["ev-slack-seats", "ev-slack-usage", "ev-roster", "ev-slack-contract"],
        "draft_to": "renewals@slack.com",
        "draft_subject": "Slack renewal true-down request for AcmeAI",
        "draft_body": """Hi Slack Account Team,

AcmeAI completed a 90-day usage review and confirmed the required license changes directly with resource owners.

Please provide a revised order form that:
- Removes 84 owner-confirmed no-use Pro seats
- Downgrades 47 owner-confirmed low-use seats to the lowest suitable paid tier
- Retains 89 active Pro seats
- Applies any available prorated credits

Please confirm the effective date, revised annual commitment, and credit amount by June 19, 2026.

Regards,
AcmeAI Procurement""",
    },
    "datadog-renegotiate": {
        "id": "datadog-contract-review",
        "title": "Recover the Datadog billing variance",
        "action": "Create an evidence-backed vendor dispute requesting an $18,000 credit and revised terms.",
        "urgency": "this_week",
        "rationale": "Four invoices exceed the contracted baseline by $4,500 each, with competitor benchmarks strengthening the dispute.",
        "evidence_refs": ["ev-datadog-contract", "ev-datadog-invoices", "ev-datadog-overlap"],
        "draft_to": "billing@datadoghq.com",
        "draft_subject": "Request for $18,000 credit and revised Datadog order form",
        "draft_body": """Hi Datadog Billing and Account Team,

Our review identified four invoices that each exceed AcmeAI's contracted baseline by $4,500, for a total variance of $18,000.

Please provide:
- A credit memo for the $18,000 overbilling variance
- A line-item reconciliation against the current order form
- A revised order form that prevents the variance from recurring
- Updated commercial terms reflecting current Grafana Cloud and New Relic benchmarks

Please acknowledge this dispute and provide the credit and revised terms within five business days.

Regards,
AcmeAI Finance and Procurement""",
    },
    "figma-renewal-stop": {
        "id": "figma-renewal-stop",
        "title": "Stop the unused Figma renewal",
        "action": "Create a formal vendor non-renewal draft before the notice deadline.",
        "urgency": "before_renewal",
        "rationale": "Zero recorded usage and design-manager confirmation make non-renewal a high-confidence, low-risk recovery.",
        "evidence_refs": ["ev-figma-usage", "ev-figma-contract"],
        "draft_to": "support@figma.com",
        "draft_subject": "Formal Figma non-renewal notice for AcmeAI Professional workspace",
        "draft_body": """Hi Figma Account Team,

This email is formal notice that AcmeAI does not intend to renew the unused Professional workspace covered by our current agreement.

Please:
- Remove the 12 unused Professional seats
- Prevent any automatic renewal or additional billing
- Confirm the effective termination date
- Confirm that no further invoices will be issued after termination

Please acknowledge this non-renewal notice within three business days and before the July 15 notice deadline.

Regards,
AcmeAI Procurement""",
    },
}


def build_recovery_tasks(
    strategies: list[Strategy] | None = None,
    figma_verification: TaskVerification | None = None,
) -> list[RecoveryTask]:
    if strategies is None:
        from app.fixtures.demo_data import STRATEGIES
        from app.services.detection import gate_strategy

        strategies = deepcopy(STRATEGIES)
        for strategy in strategies:
            strategy.approved = gate_strategy(strategy)

    tasks = []
    for strategy in strategies:
        blueprint = TASK_BLUEPRINTS.get(strategy.id)
        if not strategy.approved or not blueprint:
            continue
        task = RecoveryTask(
            strategy_id=strategy.id,
            vendor=strategy.vendor,
            savings=strategy.savings,
            recommendation="approve",
            gate_confidence=strategy.scores.confidence,
            gate_action_safety=strategy.scores.action_safety,
            **blueprint,
        )
        if strategy.id == "figma-renewal-stop" and figma_verification:
            task.status = "awaiting_verification"
            task.verification = deepcopy(figma_verification)
        tasks.append(task)
    return sorted(tasks, key=lambda task: (task.id != "figma-renewal-stop", task.id))
