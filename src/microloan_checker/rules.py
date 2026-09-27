"""Deterministic checks for the rule-only baseline.

The baseline checks completeness, input validity, and exact consistency. It
does not interpret the meaning of the free-text loan purpose.
"""

from __future__ import annotations

from .models import Application, RuleIssue, RuleResult, UserOutput


def _issue(
    code: str,
    output: UserOutput,
    reason: str,
    *evidence_fields: str,
) -> RuleIssue:
    return RuleIssue(
        code=code,
        output=output,
        reason=reason,
        evidence_fields=tuple(evidence_fields),
    )


def run_rule_baseline(application: Application) -> RuleResult:
    issues: list[RuleIssue] = []

    if not application.identity_proof_present:
        issues.append(
            _issue(
                "MISSING_IDENTITY_PROOF",
                UserOutput.MISSING_DOCUMENTS,
                "Identity proof is missing.",
                "identity_proof_present",
            )
        )

    if not application.income_proof_present:
        issues.append(
            _issue(
                "MISSING_INCOME_PROOF",
                UserOutput.MISSING_DOCUMENTS,
                "Income proof is missing.",
                "income_proof_present",
            )
        )

    if not application.bank_statement_present:
        issues.append(
            _issue(
                "MISSING_BANK_STATEMENT",
                UserOutput.MISSING_DOCUMENTS,
                "Bank statement is missing.",
                "bank_statement_present",
            )
        )

    required_values = {
        "declared_monthly_income": application.declared_monthly_income,
        "requested_loan_amount": application.requested_loan_amount,
        "existing_monthly_liabilities": application.existing_monthly_liabilities,
        "loan_purpose_category": application.loan_purpose_category,
        "loan_purpose_text": application.loan_purpose_text,
    }
    for field_name, value in required_values.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            issues.append(
                _issue(
                    "MISSING_REQUIRED_FIELD",
                    UserOutput.MISSING_DOCUMENTS,
                    f"Required field is missing: {field_name}.",
                    field_name,
                )
            )

    if application.income_proof_present and application.income_proof_monthly_income is None:
        issues.append(
            _issue(
                "MISSING_REQUIRED_FIELD",
                UserOutput.MISSING_DOCUMENTS,
                "Income proof is present but its normalized monthly income is missing.",
                "income_proof_present",
                "income_proof_monthly_income",
            )
        )
    if not application.income_proof_present and application.income_proof_monthly_income is not None:
        issues.append(
            _issue(
                "DOCUMENT_FIELD_CONTRADICTION",
                UserOutput.INCONSISTENT_INFORMATION,
                "Income proof is marked absent but an income-proof value is present.",
                "income_proof_present",
                "income_proof_monthly_income",
            )
        )

    if application.bank_statement_present and application.bank_statement_average_monthly_inflow is None:
        issues.append(
            _issue(
                "MISSING_REQUIRED_FIELD",
                UserOutput.MISSING_DOCUMENTS,
                "Bank statement is present but its normalized monthly inflow is missing.",
                "bank_statement_present",
                "bank_statement_average_monthly_inflow",
            )
        )
    if not application.bank_statement_present and application.bank_statement_average_monthly_inflow is not None:
        issues.append(
            _issue(
                "DOCUMENT_FIELD_CONTRADICTION",
                UserOutput.INCONSISTENT_INFORMATION,
                "Bank statement is marked absent but a bank-statement value is present.",
                "bank_statement_present",
                "bank_statement_average_monthly_inflow",
            )
        )

    numeric_values = {
        "declared_monthly_income": application.declared_monthly_income,
        "income_proof_monthly_income": application.income_proof_monthly_income,
        "bank_statement_average_monthly_inflow": application.bank_statement_average_monthly_inflow,
        "existing_monthly_liabilities": application.existing_monthly_liabilities,
    }
    for field_name, value in numeric_values.items():
        if value is not None and value < 0:
            issues.append(
                _issue(
                    "INVALID_NUMERIC_VALUE",
                    UserOutput.INCONSISTENT_INFORMATION,
                    f"Numeric field cannot be negative: {field_name}.",
                    field_name,
                )
            )

    if (
        application.requested_loan_amount is not None
        and application.requested_loan_amount <= 0
    ):
        issues.append(
            _issue(
                "INVALID_NUMERIC_VALUE",
                UserOutput.INCONSISTENT_INFORMATION,
                "Requested loan amount must be greater than zero.",
                "requested_loan_amount",
            )
        )

    if (
        application.income_proof_present
        and application.declared_monthly_income is not None
        and application.income_proof_monthly_income is not None
        and application.declared_monthly_income
        != application.income_proof_monthly_income
    ):
        issues.append(
            _issue(
                "DECLARED_INCOME_MISMATCH",
                UserOutput.INCONSISTENT_INFORMATION,
                "Declared monthly income does not match the normalized income-proof value.",
                "declared_monthly_income",
                "income_proof_monthly_income",
            )
        )

    if (
        application.bank_statement_present
        and application.declared_monthly_income is not None
        and application.bank_statement_average_monthly_inflow is not None
        and application.declared_monthly_income
        != application.bank_statement_average_monthly_inflow
    ):
        issues.append(
            _issue(
                "BANK_INFLOW_MISMATCH",
                UserOutput.INCONSISTENT_INFORMATION,
                "Declared monthly income does not match the normalized bank-statement inflow.",
                "declared_monthly_income",
                "bank_statement_average_monthly_inflow",
            )
        )

    output_order = (
        UserOutput.MISSING_DOCUMENTS,
        UserOutput.INCONSISTENT_INFORMATION,
        UserOutput.MANUAL_REVIEW,
    )
    outputs = tuple(
        output for output in output_order if any(issue.output == output for issue in issues)
    )
    if not outputs:
        outputs = (UserOutput.COMPLETE,)

    return RuleResult(
        application_id=application.application_id,
        outputs=outputs,
        issues=tuple(issues),
    )
