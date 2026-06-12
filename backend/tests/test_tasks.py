from app.services.tasks import build_recovery_tasks
from app.models.schemas import TaskVerification


def test_recovery_tasks_are_clear_and_actionable():
    tasks = build_recovery_tasks()
    assert len(tasks) == 3
    assert sum(task.savings for task in tasks) == 47_600
    assert all(task.owner == "Project Head" for task in tasks)
    assert all(task.status == "pending_approval" for task in tasks)
    assert all(task.evidence_refs for task in tasks)
    assert all(task.draft_to and task.draft_subject and task.draft_body for task in tasks)
    assert {task.strategy_id for task in tasks} == {"slack-downgrade", "datadog-renegotiate", "figma-renewal-stop"}
    assert all(task.gate_action_safety >= 0.85 and task.gate_confidence >= 0.90 for task in tasks)


def test_blocked_strategies_never_create_recovery_tasks():
    from copy import deepcopy

    from app.fixtures.demo_data import STRATEGIES
    from app.services.detection import gate_strategy

    strategies = deepcopy(STRATEGIES)
    for strategy in strategies:
        strategy.approved = gate_strategy(strategy)
    tasks = build_recovery_tasks(strategies)
    assert "slack-cancel" not in {task.strategy_id for task in tasks}
    assert "slack-renegotiate" not in {task.strategy_id for task in tasks}


def test_live_figma_verification_is_first_and_blocks_approval():
    tasks = build_recovery_tasks(figma_verification=TaskVerification(thread_ts="123.456", channel_id="C123"))
    assert tasks[0].id == "figma-renewal-stop"
    assert tasks[0].status == "awaiting_verification"
    assert tasks[0].verification.thread_ts == "123.456"
