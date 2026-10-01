"""Public API for the microloan application readiness checker.

Exports the core application/result models and ``run_rule_baseline`` while
keeping optional live Gemini and RAG dependencies out of package import time.
"""

from .models import Application, PurposeCategory, RuleResult, UserOutput
from .rules import run_rule_baseline

__all__ = [
    "Application",
    "PurposeCategory",
    "RuleResult",
    "UserOutput",
    "run_rule_baseline",
]
