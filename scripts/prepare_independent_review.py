"""Prepare blind label and citation-support packs for an external reviewer."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / "independent_review"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def prepare() -> None:
    applications = {
        row["application_id"]: row
        for row in _read_jsonl(
            PROJECT_ROOT / "data" / "final_test" / "applications.jsonl"
        )
    }
    results = json.loads(
        (PROJECT_ROOT / "results" / "rag_final_test.json").read_text(
            encoding="utf-8"
        )
    )
    handwritten = [
        row
        for row in results["predictions"]
        if row["eval_slice"] == "handwritten_semantic_contradiction"
    ]
    if len(handwritten) != 15:
        raise ValueError(f"Expected 15 handwritten cases, found {len(handwritten)}")

    blind_rows = []
    citation_rows = []
    for prediction in handwritten:
        application_id = prediction["application_id"]
        application = applications[application_id]
        blind_rows.append(
            {
                "application_id": application_id,
                "loan_purpose_category": application["loan_purpose_category"],
                "loan_purpose_text": application["loan_purpose_text"],
                "reviewer_readiness_output": "",
                "reviewer_issue_code": "",
                "reviewer_evidence_fields": "",
                "reviewer_confidence_high_medium_low": "",
                "reviewer_notes": "",
            }
        )

        result = prediction["result"]
        retrieval = result["retrieval"]
        cited_ids = retrieval["cited_chunk_ids"]
        retrieved_by_id = {
            item["chunk_id"]: item for item in retrieval["retrieved_chunks"]
        }
        cited_text = "\n\n".join(
            f"[{chunk_id}] {retrieved_by_id[chunk_id]['text']}"
            for chunk_id in cited_ids
        )
        semantic = result["semantic_result"]
        citation_rows.append(
            {
                "application_id": application_id,
                "loan_purpose_category": application["loan_purpose_category"],
                "loan_purpose_text": application["loan_purpose_text"],
                "system_outputs": " | ".join(prediction["predicted_outputs"]),
                "semantic_issue_codes": " | ".join(
                    semantic.get("semantic_issue_codes", [])
                ),
                "model_reason": semantic.get("reason", ""),
                "cited_chunk_ids": " | ".join(cited_ids),
                "cited_text": cited_text,
                "reviewer_support_supported_partial_unsupported": "",
                "reviewer_unsupported_or_missing_claims": "",
                "reviewer_notes": "",
            }
        )

    _write_csv(
        REVIEW_ROOT / "stage1_blind_semantic_review.csv",
        blind_rows,
        list(blind_rows[0]),
    )
    _write_csv(
        REVIEW_ROOT / "stage2_citation_support_review.csv",
        citation_rows,
        list(citation_rows[0]),
    )
    print(f"blind_cases={len(blind_rows)}")
    print(f"citation_cases={len(citation_rows)}")


if __name__ == "__main__":
    prepare()
