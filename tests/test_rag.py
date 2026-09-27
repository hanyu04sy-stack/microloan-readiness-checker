from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.models import Application, UserOutput  # noqa: E402
from microloan_checker.rag import (  # noqa: E402
    build_rag_prompt,
    build_retrieval_query,
    run_rag_hybrid,
)
from microloan_checker.retrieval import ProjectKnowledgeRetriever  # noqa: E402
from microloan_checker.semantic import ModelCall  # noqa: E402


KNOWLEDGE_ROOT = PROJECT_ROOT / "knowledge_base"


def load_application(application_id: str) -> Application:
    path = PROJECT_ROOT / "data" / "final_test" / "applications.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["application_id"] == application_id:
            return Application.from_mapping(record)
    raise LookupError(application_id)


class MockRagClient:
    def __init__(self, citation: str | None = None):
        self.citation = citation
        self.last_prompt = ""
        self.last_schema = None

    def generate_structured(self, *, prompt, response_schema):
        self.last_prompt = prompt
        self.last_schema = response_schema
        allowed = response_schema["properties"]["source_chunk_ids"]["items"]["enum"]
        return ModelCall(
            payload={
                "semantic_issue_codes": ["PURPOSE_CATEGORY_CONTRADICTION"],
                "manual_review_required": False,
                "reason": "The purpose text describes a vehicle use, not education.",
                "evidence_fields": ["loan_purpose_category", "loan_purpose_text"],
                "source_chunk_ids": [self.citation or allowed[0]],
            },
            model="mock-rag-model",
            prompt_tokens=150,
            output_tokens=40,
            total_tokens=190,
            latency_ms=8.0,
        )


class RagTests(unittest.TestCase):
    def test_retrieval_returns_semantic_policy_for_handwritten_case(self):
        application = load_application("APP_0286")
        retriever = ProjectKnowledgeRetriever(KNOWLEDGE_ROOT)
        retrieved = retriever.retrieve(build_retrieval_query(application), top_k=3)
        ids = [item.chunk.chunk_id for item in retrieved]
        self.assertEqual(
            ids,
            [
                "project_readiness_contract#purpose-category-meanings",
                "project_readiness_contract#semantic-category-decision-rules",
                "project_readiness_contract#semantic-issue-definitions",
            ],
        )

    def test_rag_prompt_contains_sources_but_not_ground_truth(self):
        application = load_application("APP_0286")
        retrieved = ProjectKnowledgeRetriever(KNOWLEDGE_ROOT).retrieve(
            build_retrieval_query(application), top_k=3
        )
        prompt = build_rag_prompt(application, retrieved)
        self.assertIn("SOURCE_ID:", prompt)
        self.assertIn("not real bank policy", prompt)
        self.assertNotIn("expected_outputs", prompt)
        self.assertNotIn("label_rationale", prompt)

    def test_rag_result_preserves_citations_and_hybrid_output(self):
        application = load_application("APP_0286")
        result = run_rag_hybrid(
            application,
            MockRagClient(),
            knowledge_root=KNOWLEDGE_ROOT,
        )
        payload = result.to_dict()
        self.assertEqual(
            result.hybrid_result.outputs,
            (UserOutput.INCONSISTENT_INFORMATION,),
        )
        self.assertEqual(payload["system"], "rules_plus_rag_llm")
        self.assertTrue(payload["retrieval"]["cited_chunk_ids"])
        self.assertEqual(len(payload["retrieval"]["retrieved_chunks"]), 3)

    def test_unknown_rag_citation_routes_to_manual_review(self):
        application = load_application("APP_0286")
        result = run_rag_hybrid(
            application,
            MockRagClient(citation="unknown#source"),
            knowledge_root=KNOWLEDGE_ROOT,
        )
        self.assertEqual(
            result.hybrid_result.outputs,
            (UserOutput.MANUAL_REVIEW,),
        )
        self.assertEqual(result.hybrid_result.semantic_result.status, "error")


if __name__ == "__main__":
    unittest.main()
