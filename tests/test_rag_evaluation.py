from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from evaluate_rag import _citation_metrics, _security_suite_metrics  # noqa: E402


class RagEvaluationMetricTests(unittest.TestCase):
    def test_fixed_security_suite_metrics_are_complete(self):
        metrics = _security_suite_metrics()
        self.assertEqual(metrics["malicious_cases"], 6)
        self.assertEqual(metrics["benign_cases"], 6)
        self.assertEqual(metrics["malicious_suite_block_rate"], 1.0)
        self.assertEqual(metrics["benign_suite_pass_rate"], 1.0)

    def test_citation_metrics_use_only_successful_rag_responses(self):
        predictions = [
            {
                "result": {
                    "semantic_result": {"status": "success"},
                    "security": {"prompt_injection_detected": False},
                    "retrieval": {
                        "retrieved_chunks": [
                            {"chunk_id": "policy#one"},
                            {"chunk_id": "policy#two"},
                        ],
                        "cited_chunk_ids": ["policy#one"],
                    },
                }
            },
            {
                "result": {
                    "semantic_result": {"status": "error"},
                    "security": {"prompt_injection_detected": False},
                    "retrieval": {
                        "retrieved_chunks": [{"chunk_id": "policy#one"}],
                        "cited_chunk_ids": [],
                    },
                }
            },
        ]
        metrics = _citation_metrics(predictions)
        self.assertEqual(metrics["successful_rag_responses"], 1)
        self.assertEqual(metrics["citation_coverage"], 1.0)
        self.assertEqual(metrics["citation_validity"], 1.0)
        self.assertEqual(metrics["retrieval_coverage"], 1.0)


if __name__ == "__main__":
    unittest.main()
