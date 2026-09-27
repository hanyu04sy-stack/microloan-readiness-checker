"""Semantic-checking contract shared by mock and Gemini clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .models import Application, DataValidationError, SemanticIssueCode


SEMANTIC_EVIDENCE_FIELDS = frozenset(
    {
        "declared_monthly_income",
        "requested_loan_amount",
        "existing_monthly_liabilities",
        "loan_purpose_category",
        "loan_purpose_text",
    }
)

SEMANTIC_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "semantic_issue_codes": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [code.value for code in SemanticIssueCode],
            },
        },
        "manual_review_required": {"type": "boolean"},
        "reason": {"type": "string"},
        "evidence_fields": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": sorted(SEMANTIC_EVIDENCE_FIELDS),
            },
        },
    },
    "required": [
        "semantic_issue_codes",
        "manual_review_required",
        "reason",
        "evidence_fields",
    ],
}


@dataclass(frozen=True)
class ModelCall:
    payload: Mapping[str, Any]
    model: str
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    attempt_count: int = 1
    retry_errors: tuple[str, ...] = ()


class SemanticModelClient(Protocol):
    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: Mapping[str, Any],
    ) -> ModelCall:
        """Return one model call constrained by the supplied JSON schema."""


@dataclass(frozen=True)
class SemanticAssessment:
    issue_codes: tuple[SemanticIssueCode, ...]
    manual_review_required: bool
    reason: str
    evidence_fields: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SemanticAssessment":
        expected_keys = {
            "semantic_issue_codes",
            "manual_review_required",
            "reason",
            "evidence_fields",
        }
        actual_keys = set(payload)
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            raise DataValidationError(
                f"Semantic response keys do not match schema; missing={missing}, extra={extra}"
            )

        raw_codes = payload["semantic_issue_codes"]
        if not isinstance(raw_codes, list) or any(
            not isinstance(item, str) for item in raw_codes
        ):
            raise DataValidationError("semantic_issue_codes must be a list of strings")
        if len(raw_codes) != len(set(raw_codes)):
            raise DataValidationError("semantic_issue_codes must not contain duplicates")
        try:
            issue_codes = tuple(SemanticIssueCode(item) for item in raw_codes)
        except ValueError as exc:
            raise DataValidationError("Semantic response contains an unknown issue code") from exc

        manual_review_required = payload["manual_review_required"]
        if not isinstance(manual_review_required, bool):
            raise DataValidationError("manual_review_required must be true or false")

        reason = payload["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise DataValidationError("reason must be a non-empty string")

        raw_evidence = payload["evidence_fields"]
        if not isinstance(raw_evidence, list) or any(
            not isinstance(item, str) for item in raw_evidence
        ):
            raise DataValidationError("evidence_fields must be a list of strings")
        if len(raw_evidence) != len(set(raw_evidence)):
            raise DataValidationError("evidence_fields must not contain duplicates")
        unknown_evidence = set(raw_evidence) - SEMANTIC_EVIDENCE_FIELDS
        if unknown_evidence:
            raise DataValidationError(
                f"Semantic response cites unsupported fields: {sorted(unknown_evidence)}"
            )

        manual_codes = {
            SemanticIssueCode.VAGUE_LOAN_PURPOSE,
            SemanticIssueCode.INSUFFICIENT_SEMANTIC_EVIDENCE,
        }
        contains_manual_code = any(code in manual_codes for code in issue_codes)
        if contains_manual_code != manual_review_required:
            raise DataValidationError(
                "manual_review_required must match vague or insufficient-evidence codes"
            )
        if issue_codes and not raw_evidence:
            raise DataValidationError("An identified semantic issue must cite evidence fields")
        if not issue_codes and raw_evidence:
            raise DataValidationError("A no-issue response must not cite evidence fields")

        return cls(
            issue_codes=issue_codes,
            manual_review_required=manual_review_required,
            reason=reason.strip(),
            evidence_fields=tuple(raw_evidence),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_issue_codes": [code.value for code in self.issue_codes],
            "manual_review_required": self.manual_review_required,
            "reason": self.reason,
            "evidence_fields": list(self.evidence_fields),
        }


@dataclass(frozen=True)
class SemanticCheckResult:
    status: str
    assessment: SemanticAssessment | None
    model_call: ModelCall | None
    error: str | None

    @classmethod
    def success(
        cls, assessment: SemanticAssessment, model_call: ModelCall
    ) -> "SemanticCheckResult":
        return cls(
            status="success",
            assessment=assessment,
            model_call=model_call,
            error=None,
        )

    @classmethod
    def failure(cls, error: str) -> "SemanticCheckResult":
        return cls(status="error", assessment=None, model_call=None, error=error)


class SemanticChecker:
    """Runs exactly one structured semantic-model call per application."""

    def __init__(self, client: SemanticModelClient):
        self.client = client

    def check(self, application: Application) -> SemanticCheckResult:
        prompt = build_semantic_prompt(application)
        try:
            model_call = self.client.generate_structured(
                prompt=prompt,
                response_schema=SEMANTIC_RESPONSE_SCHEMA,
            )
            assessment = SemanticAssessment.from_mapping(model_call.payload)
            return SemanticCheckResult.success(assessment, model_call)
        except Exception as exc:
            return SemanticCheckResult.failure(
                f"{type(exc).__name__}: {exc}"
            )


def semantic_application_payload(application: Application) -> dict[str, Any]:
    """Return only fields needed for semantic comparison."""

    return {
        "declared_monthly_income": application.declared_monthly_income,
        "requested_loan_amount": application.requested_loan_amount,
        "existing_monthly_liabilities": application.existing_monthly_liabilities,
        "loan_purpose_category": (
            application.loan_purpose_category.value
            if application.loan_purpose_category is not None
            else None
        ),
        "loan_purpose_text": application.loan_purpose_text,
    }


def build_semantic_prompt(application: Application) -> str:
    import json

    payload = semantic_application_payload(application)
    return (
        "You are checking application-material readiness before formal credit assessment.\n"
        "Your task is limited to the meaning of the supplied loan-purpose text and its "
        "consistency with the supplied structured fields.\n\n"
        "Allowed findings:\n"
        "- VAGUE_LOAN_PURPOSE: the use of funds is not specific enough to check.\n"
        "- PURPOSE_CATEGORY_CONTRADICTION: the text clearly describes a materially "
        "different purpose category.\n"
        "- PURPOSE_FORM_CONTRADICTION: the text directly contradicts another supplied "
        "field and detecting it requires interpreting meaning.\n"
        "- INSUFFICIENT_SEMANTIC_EVIDENCE: more than one reasonable interpretation remains.\n\n"
        "Do not assess affordability, creditworthiness, approval, rejection, interest, "
        "limits, default risk, or whether a purpose is wise. Do not invent missing facts. "
        "An unusual purpose is not a contradiction. If evidence is insufficient, require "
        "manual review. Cite only supplied field names.\n\n"
        "Output invariants:\n"
        "- If there is no semantic issue, return semantic_issue_codes=[], "
        "manual_review_required=false, and evidence_fields=[].\n"
        "- For PURPOSE_CATEGORY_CONTRADICTION or PURPOSE_FORM_CONTRADICTION, "
        "manual_review_required=false and evidence_fields must cite the supplied fields "
        "that establish the contradiction.\n"
        "- For VAGUE_LOAN_PURPOSE or INSUFFICIENT_SEMANTIC_EVIDENCE, "
        "manual_review_required=true and evidence_fields must cite the supplied fields "
        "that make review necessary.\n\n"
        "Application fields:\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
    )
