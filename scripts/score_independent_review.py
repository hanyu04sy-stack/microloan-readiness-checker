"""Validate and summarize a completed two-stage independent review."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / "independent_review"
ALLOWED_OUTPUTS = {
    "Complete",
    "Missing Documents",
    "Inconsistent Information",
    "Manual Review",
}
ALLOWED_SUPPORT = {"SUPPORTED", "PARTIAL", "UNSUPPORTED"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def score() -> dict:
    stage1 = _read_csv(REVIEW_ROOT / "stage1_blind_semantic_review.csv")
    stage2 = _read_csv(REVIEW_ROOT / "stage2_citation_support_review.csv")
    if len(stage1) != 15 or len(stage2) != 15:
        raise ValueError("Both review stages must contain exactly 15 cases")
    labels = {
        row["application_id"]: row
        for row in _read_jsonl(
            PROJECT_ROOT / "data" / "final_test" / "labels.jsonl"
        )
    }
    missing_stage1 = [
        row["application_id"]
        for row in stage1
        if row["reviewer_readiness_output"] not in ALLOWED_OUTPUTS
    ]
    normalized_support = [
        row["reviewer_support_supported_partial_unsupported"].strip().upper()
        for row in stage2
    ]
    missing_stage2 = [
        row["application_id"]
        for row, value in zip(stage2, normalized_support)
        if value not in ALLOWED_SUPPORT
    ]
    if missing_stage1 or missing_stage2:
        raise ValueError(
            "Review is incomplete; "
            f"stage1={missing_stage1}, stage2={missing_stage2}"
        )
    exact_output_matches = sum(
        row["reviewer_readiness_output"]
        in labels[row["application_id"]]["expected_outputs"]
        for row in stage1
    )
    support_counts = Counter(normalized_support)
    return {
        "review_status": "complete",
        "cases_reviewed": 15,
        "blind_output_agreement_count": exact_output_matches,
        "blind_output_agreement_rate": exact_output_matches / 15,
        "citation_support_counts": dict(sorted(support_counts.items())),
        "citation_fully_supported_rate": support_counts["SUPPORTED"] / 15,
        "note": (
            "This summary measures agreement and citation support; it does not "
            "convert one reviewer into authoritative bank policy."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(score(), ensure_ascii=False, indent=2, sort_keys=True))
