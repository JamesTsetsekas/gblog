"""Synthetic patch rollout model. No real advisory, no real fleet, no network."""
from .model import ADVISORY, Fleet, classify, naive_classification, load_fleet  # noqa: F401
from .rollout import build_plan, in_scope, mitigate, remediate, run_rollout, verify  # noqa: F401
