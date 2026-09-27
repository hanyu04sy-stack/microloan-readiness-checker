from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.models import (  # noqa: E402
    Application,
    DataValidationError,
    UserOutput,
)
from microloan_checker.rules import run_rule_baseline  # noqa: E402


def valid_record() -> dict:
    return {
        "application_id": "APP-0001",
        "declared_monthly_income": 4000,
        "income_proof_monthly_income": 4000,
        "bank_statement_average_monthly_inflow": 4000,
        "requested_loan_amount": 8000,
        "existing_monthly_liabilities": 500,
        "loan_purpose_category": "EDUCATION",
        "loan_purpose_text": "Payment for a professional course fee.",
        "identity_proof_present": True,
        "income_proof_present": True,
        "bank_statement_present": True,
    }


class RuleBaselineTests(unittest.TestCase):
    def evaluate(self, changes: dict | None = None):
        record = valid_record()
        record.update(changes or {})
        return run_rule_baseline(Application.from_mapping(record))

    def test_complete_application(self):
        result = self.evaluate()
        self.assertEqual(result.outputs, (UserOutput.COMPLETE,))
        self.assertFalse(result.flag_worthy)
        self.assertEqual(result.issues, ())

    def test_missing_document(self):
        result = self.evaluate(
            {
                "income_proof_present": False,
                "income_proof_monthly_income": None,
            }
        )
        self.assertIn(UserOutput.MISSING_DOCUMENTS, result.outputs)
        self.assertIn("MISSING_INCOME_PROOF", [issue.code for issue in result.issues])

    def test_income_mismatch(self):
        result = self.evaluate({"income_proof_monthly_income": 3500})
        self.assertIn(UserOutput.INCONSISTENT_INFORMATION, result.outputs)
        self.assertIn("DECLARED_INCOME_MISMATCH", [issue.code for issue in result.issues])

    def test_absent_document_with_value_preserves_multiple_outputs(self):
        result = self.evaluate({"bank_statement_present": False})
        self.assertEqual(
            result.outputs,
            (
                UserOutput.MISSING_DOCUMENTS,
                UserOutput.INCONSISTENT_INFORMATION,
            ),
        )
        self.assertIn("MISSING_BANK_STATEMENT", [issue.code for issue in result.issues])
        self.assertIn(
            "DOCUMENT_FIELD_CONTRADICTION", [issue.code for issue in result.issues]
        )

    def test_blank_purpose_is_missing_required_field(self):
        result = self.evaluate({"loan_purpose_text": "  "})
        self.assertIn(UserOutput.MISSING_DOCUMENTS, result.outputs)
        self.assertIn("MISSING_REQUIRED_FIELD", [issue.code for issue in result.issues])

    def test_negative_liabilities_are_invalid_not_credit_scored(self):
        result = self.evaluate({"existing_monthly_liabilities": -1})
        self.assertIn(UserOutput.INCONSISTENT_INFORMATION, result.outputs)
        self.assertIn("INVALID_NUMERIC_VALUE", [issue.code for issue in result.issues])

    def test_unknown_purpose_category_is_rejected_by_schema(self):
        record = valid_record()
        record["loan_purpose_category"] = "UNDEFINED_CATEGORY"
        with self.assertRaises(DataValidationError):
            Application.from_mapping(record)

    def test_evaluation_metadata_is_ignored(self):
        record = valid_record()
        record.update(
            {
                "expected_outputs": ["Inconsistent Information"],
                "flag_worthy": True,
                "label_rationale": "This must never reach the baseline.",
                "case_source": "handwritten_semantic",
                "split": "test",
            }
        )
        result = run_rule_baseline(Application.from_mapping(record))
        self.assertEqual(result.outputs, (UserOutput.COMPLETE,))


if __name__ == "__main__":
    unittest.main()
