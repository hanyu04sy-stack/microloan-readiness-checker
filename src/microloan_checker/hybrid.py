"""Merge deterministic rules with a structured semantic assessment.

Exports ``HybridResult`` and ``run_hybrid``; semantic failures must fail closed
to manual review and can never remove deterministic findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Application, SemanticIssueCode, UserOutput
from .rules import run_rule_baseline
from .semantic import SemanticCheckResult, SemanticChecker


@dataclass(frozen=True)
class HybridResult:
    application_id: str
    outputs: tuple[UserOutput, ...]
    rule_result: Any
    semantic_result: SemanticCheckResult

    @property
    def flag_worthy(self) -> bool:
        return self.outputs != (UserOutput.COMPLETE,)

    def to_dict(self) -> dict[str, Any]:
        semantic_payload: dict[str, Any]
        if self.semantic_result.assessment is not None:
            semantic_payload = {
                "status": "success",
                **self.semantic_result.assessment.to_dict(),
            }
        else:
            semantic_payload = {
                "status": "error",
                "error": self.semantic_result.error,
                "fallback": UserOutput.MANUAL_REVIEW.value,
            }

        call = self.semantic_result.model_call
        model_call = None
        if call is not None:
            model_call = {
                "model": call.model,
                "prompt_tokens": call.prompt_tokens,
                "output_tokens": call.output_tokens,
                "total_tokens": call.total_tokens,
                "latency_ms": call.latency_ms,
                "attempt_count": call.attempt_count,
                "retry_errors": list(call.retry_errors),
            }

        return {
            "application_id": self.application_id,
            "system": "rules_plus_llm",
            "outputs": [output.value for output in self.outputs],
            "flag_worthy": self.flag_worthy,
            "rule_result": self.rule_result.to_dict(),
            "semantic_result": semantic_payload,
            "model_call": model_call,
        }


def run_hybrid(application: Application, checker: SemanticChecker) -> HybridResult:
    rule_result = run_rule_baseline(application)
    semantic_result = checker.check(application)

    outputs = {output for output in rule_result.outputs if output != UserOutput.COMPLETE}
    assessment = semantic_result.assessment
    if assessment is None:
        outputs.add(UserOutput.MANUAL_REVIEW)
    else:
        contradiction_codes = {
            SemanticIssueCode.PURPOSE_CATEGORY_CONTRADICTION,
            SemanticIssueCode.PURPOSE_FORM_CONTRADICTION,
        }
        if any(code in contradiction_codes for code in assessment.issue_codes):
            outputs.add(UserOutput.INCONSISTENT_INFORMATION)
        if assessment.manual_review_required:
            outputs.add(UserOutput.MANUAL_REVIEW)

    output_order = (
        UserOutput.MISSING_DOCUMENTS,
        UserOutput.INCONSISTENT_INFORMATION,
        UserOutput.MANUAL_REVIEW,
    )
    ordered_outputs = tuple(output for output in output_order if output in outputs)
    if not ordered_outputs:
        ordered_outputs = (UserOutput.COMPLETE,)

    return HybridResult(
        application_id=application.application_id,
        outputs=ordered_outputs,
        rule_result=rule_result,
        semantic_result=semantic_result,
    )
