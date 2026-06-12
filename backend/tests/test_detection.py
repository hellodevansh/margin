from app.fixtures.demo_data import METRICS
from app.services.detection import compute_potential_leakage, gate_strategy, verify_employees
from app.fixtures.demo_data import STRATEGIES


def test_required_metrics_are_stable():
    assert METRICS.potential_leakage == 111_840
    assert METRICS.verified_recoverable == 82_300
    assert METRICS.redundancy_savings == 24_000
    assert METRICS.negotiation_leverage == 92


def test_detected_leaks_sum_to_potential_leakage():
    assert compute_potential_leakage() == 111_840


def test_gate_requires_both_thresholds():
    assert gate_strategy(STRATEGIES[1]) is True
    assert gate_strategy(STRATEGIES[0]) is False
    assert gate_strategy(STRATEGIES[2]) is False
    assert gate_strategy(STRATEGIES[4]) is True


def test_resource_owner_confirmations_drive_recovery_evidence():
    replies = verify_employees()
    assert len(replies) == 5
    assert {reply.interpretation for reply in replies} == {"keep", "downgrade", "reclaim"}
    assert all(reply.response for reply in replies)
