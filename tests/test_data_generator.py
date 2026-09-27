from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.models import Application  # noqa: E402
from microloan_checker.rules import run_rule_baseline  # noqa: E402
from scripts.generate_synthetic_data import build_cases  # noqa: E402
from scripts.assemble_final_test import build_final_records  # noqa: E402


class DataGeneratorTests(unittest.TestCase):
    def test_final_test_assembly_has_confirmed_composition(self):
        applications, labels = build_final_records()
        self.assertEqual(len(applications), 50)
        self.assertEqual(len(labels), 50)
        self.assertEqual(
            Counter(label["eval_slice"] for label in labels),
            Counter(
                {
                    "clean": 20,
                    "missing_document": 5,
                    "numeric_or_field_contradiction": 5,
                    "ambiguous_purpose": 5,
                    "handwritten_semantic_contradiction": 15,
                }
            ),
        )

        semantic_ids = {
            label["application_id"]
            for label in labels
            if label["eval_slice"] == "handwritten_semantic_contradiction"
        }
        for record in applications:
            if record["application_id"] in semantic_ids:
                result = run_rule_baseline(Application.from_mapping(record))
                self.assertEqual([item.value for item in result.outputs], ["Complete"])

    def test_confirmed_scripted_test_composition(self):
        counts = {
            "clean": 20,
            "missing_document": 5,
            "numeric_or_field_contradiction": 5,
            "ambiguous_purpose": 5,
        }
        cases = build_cases(
            split_name="test",
            start_index=251,
            counts=counts,
            seed=6203,
            label_status="frozen",
        )
        self.assertEqual(len(cases), 35)
        self.assertEqual(
            {case.application["application_id"] for case in cases},
            {f"APP_{index:04d}" for index in range(251, 286)},
        )
        self.assertEqual(
            Counter(case.label["eval_slice"] for case in cases), Counter(counts)
        )

    def test_application_records_exclude_ground_truth(self):
        cases = build_cases(
            split_name="validation",
            start_index=201,
            counts={"clean": 1},
            seed=6202,
            label_status="draft",
        )
        forbidden = {
            "expected_issue_codes",
            "expected_outputs",
            "flag_worthy",
            "label_rationale",
            "case_source",
            "split",
            "eval_slice",
        }
        self.assertFalse(forbidden & set(cases[0].application))

    def test_deterministic_labels_match_the_rule_baseline(self):
        counts = {
            "clean": 6,
            "missing_document": 6,
            "numeric_or_field_contradiction": 6,
        }
        cases = build_cases(
            split_name="validation",
            start_index=201,
            counts=counts,
            seed=6202,
            label_status="draft",
        )
        for case in cases:
            result = run_rule_baseline(Application.from_mapping(case.application))
            self.assertEqual(
                [output.value for output in result.outputs],
                case.label["expected_outputs"],
            )

    def test_semantic_development_cases_do_not_trigger_rules(self):
        cases = build_cases(
            split_name="development",
            start_index=1,
            counts={"ambiguous_purpose": 5, "generated_semantic_development": 5},
            seed=6201,
            label_status="draft",
        )
        for case in cases:
            result = run_rule_baseline(Application.from_mapping(case.application))
            self.assertEqual([output.value for output in result.outputs], ["Complete"])


if __name__ == "__main__":
    unittest.main()
