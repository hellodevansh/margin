from copy import deepcopy

from app.fixtures.demo_data import EMPLOYEE_REPLIES, LEAKS, REDUNDANCY, SPEND


def detect_leaks():
    return deepcopy(LEAKS)


def detect_redundancy():
    return deepcopy(REDUNDANCY)


def verify_employees():
    return deepcopy(EMPLOYEE_REPLIES)


def load_spend():
    return deepcopy(SPEND)


def compute_potential_leakage() -> int:
    return sum(leak.annual_loss for leak in LEAKS)


def gate_strategy(strategy) -> bool:
    return strategy.scores.action_safety >= 0.85 and strategy.scores.confidence >= 0.90

