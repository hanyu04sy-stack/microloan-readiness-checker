"""Tests for hybrid rule and semantic orchestration and failure handling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.hybrid import run_hybrid  # noqa: E402
from microloan_checker.models import Application, UserOutput  # noqa: E402
from microloan_checker.semantic import (  # noqa: E402
    ModelCall,
    SemanticChecker,
    build_semantic_prompt,
)


def valid_record() -> dict:
    return {
        "application_id": "APP-0100",
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


class MockClient:
    def __init__(self, payload=None, error: Exception | None = None):
        self.payload = payload
        self.error = error
        self.calls = 0
        self.last_prompt = None
        self.last_schema = None

    def generate_structured(self, *, prompt, response_schema):
        self.calls += 1
        self.last_prompt = prompt
        self.last_schema = response_schema
        if self.error is not None:
            raise self.error
        return ModelCall(
            payload=self.payload,
            model="mock-semantic-model",
            prompt_tokens=100,
            output_tokens=20,
            total_tokens=120,
            latency_ms=5.0,
        )


def no_issue_payload():
    return {
        "semantic_issue_codes": [],
        "manual_review_required": False,
        "reason": "The stated purpose is specific and consistent with the category.",
        "evidence_fields": [],
    }


class HybridTests(unittest.TestCase):
    def application(self, changes=None):
        record = valid_record()
        record.update(changes or {})
        return Application.from_mapping(record)

    def test_complete_when_rules_and_semantic_check_find_no_issue(self):
        client = MockClient(no_issue_payload())
        result = run_hybrid(self.application(), SemanticChecker(client))
        self.assertEqual(result.outputs, (UserOutput.COMPLETE,))
        self.assertEqual(client.calls, 1)

    def test_semantic_category_contradiction_is_inconsistent(self):
        client = MockClient(
            {
                "semantic_issue_codes": ["PURPOSE_CATEGORY_CONTRADICTION"],
                "manual_review_required": False,
                "reason": "The text describes a different category.",
                "evidence_fields": ["loan_purpose_category", "loan_purpose_text"],
            }
        )
        result = run_hybrid(self.application(), SemanticChecker(client))
        self.assertEqual(result.outputs, (UserOutput.INCONSISTENT_INFORMATION,))

    def test_vague_purpose_routes_to_manual_review(self):
        client = MockClient(
            {
                "semantic_issue_codes": ["VAGUE_LOAN_PURPOSE"],
                "manual_review_required": True,
                "reason": "The text does not state a concrete use of funds.",
                "evidence_fields": ["loan_purpose_text"],
            }
        )
        result = run_hybrid(self.application(), SemanticChecker(client))
        self.assertEqual(result.outputs, (UserOutput.MANUAL_REVIEW,))

    def test_rule_and_semantic_outputs_are_preserved(self):
        client = MockClient(
            {
                "semantic_issue_codes": ["PURPOSE_CATEGORY_CONTRADICTION"],
                "manual_review_required": False,
                "reason": "The text contradicts the purpose category.",
                "evidence_fields": ["loan_purpose_category", "loan_purpose_text"],
            }
        )
        application = self.application(
            {"identity_proof_present": False}
        )
        result = run_hybrid(application, SemanticChecker(client))
        self.assertEqual(
            result.outputs,
            (
                UserOutput.MISSING_DOCUMENTS,
                UserOutput.INCONSISTENT_INFORMATION,
            ),
        )

    def test_model_failure_routes_to_manual_review(self):
        client = MockClient(error=TimeoutError("simulated timeout"))
        result = run_hybrid(self.application(), SemanticChecker(client))
        self.assertEqual(result.outputs, (UserOutput.MANUAL_REVIEW,))
        self.assertEqual(result.semantic_result.status, "error")
        self.assertEqual(client.calls, 1)

    def test_invalid_structured_response_routes_to_manual_review(self):
        invalid = no_issue_payload()
        invalid["unexpected"] = "not allowed"
        client = MockClient(invalid)
        result = run_hybrid(self.application(), SemanticChecker(client))
        self.assertEqual(result.outputs, (UserOutput.MANUAL_REVIEW,))
        self.assertEqual(result.semantic_result.status, "error")

    def test_prompt_excludes_evaluation_metadata_and_document_flags(self):
        record = valid_record()
        record.update(
            {
                "expected_outputs": ["Inconsistent Information"],
                "label_rationale": "Hidden evaluation data.",
                "case_source": "handwritten_semantic",
                "split": "test",
            }
        )
        prompt = build_semantic_prompt(Application.from_mapping(record))
        self.assertNotIn("expected_outputs", prompt)
        self.assertNotIn("label_rationale", prompt)
        self.assertNotIn("case_source", prompt)
        self.assertNotIn("identity_proof_present", prompt)
        self.assertIn("loan_purpose_text", prompt)

    def test_token_metadata_is_exposed_for_later_cost_analysis(self):
        client = MockClient(no_issue_payload())
        result = run_hybrid(self.application(), SemanticChecker(client))
        exported = result.to_dict()
        self.assertEqual(exported["model_call"]["prompt_tokens"], 100)
        self.assertEqual(exported["model_call"]["output_tokens"], 20)
        self.assertEqual(exported["model_call"]["total_tokens"], 120)


if __name__ == "__main__":
    unittest.main()
