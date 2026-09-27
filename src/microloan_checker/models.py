"""Typed data structures for the rule-only baseline.

Only fields in the confirmed application contract are parsed. Ground-truth and
evaluation metadata are deliberately excluded from the Application object so
the evaluated system cannot use them as evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class DataValidationError(ValueError):
    """Raised when an input record does not match the application schema."""


class PurposeCategory(str, Enum):
    MEDICAL_EXPENSE = "MEDICAL_EXPENSE"
    EDUCATION = "EDUCATION"
    HOME_REPAIR = "HOME_REPAIR"
    SMALL_BUSINESS = "SMALL_BUSINESS"
    VEHICLE = "VEHICLE"
    DEBT_CONSOLIDATION = "DEBT_CONSOLIDATION"
    OTHER = "OTHER"


class UserOutput(str, Enum):
    COMPLETE = "Complete"
    MISSING_DOCUMENTS = "Missing Documents"
    INCONSISTENT_INFORMATION = "Inconsistent Information"
    MANUAL_REVIEW = "Manual Review"


class SemanticIssueCode(str, Enum):
    VAGUE_LOAN_PURPOSE = "VAGUE_LOAN_PURPOSE"
    PURPOSE_CATEGORY_CONTRADICTION = "PURPOSE_CATEGORY_CONTRADICTION"
    PURPOSE_FORM_CONTRADICTION = "PURPOSE_FORM_CONTRADICTION"
    INSUFFICIENT_SEMANTIC_EVIDENCE = "INSUFFICIENT_SEMANTIC_EVIDENCE"


def _required_key(record: Mapping[str, Any], key: str) -> Any:
    if key not in record:
        raise DataValidationError(f"Required key is absent: {key}")
    return record[key]


def _nullable_number(value: Any, field_name: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataValidationError(f"{field_name} must be a number or null")
    return value


def _strict_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise DataValidationError(f"{field_name} must be true or false")
    return value


def _nullable_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DataValidationError(f"{field_name} must be a string or null")
    return value


@dataclass(frozen=True)
class Application:
    application_id: str
    declared_monthly_income: float | int | None
    income_proof_monthly_income: float | int | None
    bank_statement_average_monthly_inflow: float | int | None
    requested_loan_amount: float | int | None
    existing_monthly_liabilities: float | int | None
    loan_purpose_category: PurposeCategory | None
    loan_purpose_text: str | None
    identity_proof_present: bool
    income_proof_present: bool
    bank_statement_present: bool

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "Application":
        application_id = _required_key(record, "application_id")
        if not isinstance(application_id, str) or not application_id.strip():
            raise DataValidationError("application_id must be a non-empty string")

        raw_category = _required_key(record, "loan_purpose_category")
        if raw_category is None or raw_category == "":
            category = None
        elif not isinstance(raw_category, str):
            raise DataValidationError("loan_purpose_category must be a string or null")
        else:
            try:
                category = PurposeCategory(raw_category)
            except ValueError as exc:
                allowed = ", ".join(item.value for item in PurposeCategory)
                raise DataValidationError(
                    f"loan_purpose_category must be one of: {allowed}"
                ) from exc

        return cls(
            application_id=application_id,
            declared_monthly_income=_nullable_number(
                _required_key(record, "declared_monthly_income"),
                "declared_monthly_income",
            ),
            income_proof_monthly_income=_nullable_number(
                _required_key(record, "income_proof_monthly_income"),
                "income_proof_monthly_income",
            ),
            bank_statement_average_monthly_inflow=_nullable_number(
                _required_key(record, "bank_statement_average_monthly_inflow"),
                "bank_statement_average_monthly_inflow",
            ),
            requested_loan_amount=_nullable_number(
                _required_key(record, "requested_loan_amount"),
                "requested_loan_amount",
            ),
            existing_monthly_liabilities=_nullable_number(
                _required_key(record, "existing_monthly_liabilities"),
                "existing_monthly_liabilities",
            ),
            loan_purpose_category=category,
            loan_purpose_text=_nullable_text(
                _required_key(record, "loan_purpose_text"),
                "loan_purpose_text",
            ),
            identity_proof_present=_strict_bool(
                _required_key(record, "identity_proof_present"),
                "identity_proof_present",
            ),
            income_proof_present=_strict_bool(
                _required_key(record, "income_proof_present"),
                "income_proof_present",
            ),
            bank_statement_present=_strict_bool(
                _required_key(record, "bank_statement_present"),
                "bank_statement_present",
            ),
        )


@dataclass(frozen=True)
class RuleIssue:
    code: str
    output: UserOutput
    reason: str
    evidence_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "output": self.output.value,
            "reason": self.reason,
            "evidence_fields": list(self.evidence_fields),
        }


@dataclass(frozen=True)
class RuleResult:
    application_id: str
    outputs: tuple[UserOutput, ...]
    issues: tuple[RuleIssue, ...]

    @property
    def flag_worthy(self) -> bool:
        return self.outputs != (UserOutput.COMPLETE,)

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "system": "rule_only_baseline",
            "outputs": [output.value for output in self.outputs],
            "flag_worthy": self.flag_worthy,
            "issue_codes": list(dict.fromkeys(issue.code for issue in self.issues)),
            "issues": [issue.to_dict() for issue in self.issues],
        }
