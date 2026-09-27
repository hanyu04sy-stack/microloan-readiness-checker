from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.models import Application, DataValidationError  # noqa: E402
from streamlit_app import build_record, load_application, parse_optional_number  # noqa: E402


class StreamlitAppTests(unittest.TestCase):
    def test_optional_number_parser(self):
        self.assertIsNone(parse_optional_number("  ", "amount"))
        self.assertEqual(parse_optional_number("4,000", "amount"), 4000)
        self.assertEqual(parse_optional_number("12.5", "amount"), 12.5)
        with self.assertRaises(DataValidationError):
            parse_optional_number("four thousand", "amount")

    def test_demo_loader_reads_application_input(self):
        record = load_application("APP_0286")
        self.assertEqual(record["application_id"], "APP_0286")
        self.assertNotIn("expected_outputs", record)
        self.assertNotIn("label_rationale", record)

    def test_form_mapping_matches_application_contract(self):
        record = build_record(
            {
                "application_id": " APP-WEB-1 ",
                "declared_monthly_income": "4000",
                "income_proof_monthly_income": "4000",
                "bank_statement_average_monthly_inflow": "4000",
                "requested_loan_amount": "8,000",
                "existing_monthly_liabilities": "500",
                "loan_purpose_category": "EDUCATION",
                "loan_purpose_text": "Payment for a professional course fee.",
                "identity_proof_present": True,
                "income_proof_present": True,
                "bank_statement_present": True,
            }
        )
        application = Application.from_mapping(record)
        self.assertEqual(application.application_id, "APP-WEB-1")
        self.assertEqual(application.requested_loan_amount, 8000)


if __name__ == "__main__":
    unittest.main()
