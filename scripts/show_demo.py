"""Print stable, offline evidence for the recorded demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def show_case(application_id: str) -> None:
    data_root = PROJECT_ROOT / "data" / "final_test"
    applications = {
        row["application_id"]: row
        for row in _read_jsonl(data_root / "applications.jsonl")
    }
    labels = {
        row["application_id"]: row
        for row in _read_jsonl(data_root / "labels.jsonl")
    }
    baseline = {
        row["application_id"]: row
        for row in _read_json(PROJECT_ROOT / "results" / "rule_only_final_test.json")[
            "predictions"
        ]
    }
    hybrid = {
        row["application_id"]: row
        for row in _read_json(PROJECT_ROOT / "results" / "hybrid_final_test.json")[
            "predictions"
        ]
    }
    rag = {
        row["application_id"]: row
        for row in _read_json(PROJECT_ROOT / "results" / "rag_final_test.json")[
            "predictions"
        ]
    }

    if application_id not in applications:
        raise SystemExit(f"Unknown final-test application: {application_id}")

    payload = {
        "application": applications[application_id],
        "frozen_label": labels[application_id],
        "rule_only_prediction": baseline[application_id],
        "hybrid_prediction": hybrid[application_id],
        "rag_prediction": rag[application_id],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def show_summary() -> None:
    baseline = _read_json(PROJECT_ROOT / "results" / "rule_only_final_test.json")
    hybrid = _read_json(PROJECT_ROOT / "results" / "hybrid_final_test.json")
    rag = _read_json(PROJECT_ROOT / "results" / "rag_final_test.json")
    independent_review = _read_json(
        PROJECT_ROOT / "results" / "independent_review_summary.json"
    )
    payload = {
        "release_conditions": rag["release_conditions"],
        "rule_only_full_test": baseline["metrics"]["full_test"],
        "earlier_non_rag_hybrid_full_test": hybrid["metrics"]["full_test"],
        "earlier_non_rag_hybrid_handwritten_semantic": hybrid["metrics"][
            "handwritten_semantic"
        ],
        "final_rag_full_test": rag["metrics"]["full_test"],
        "final_rag_handwritten_semantic": rag["metrics"][
            "handwritten_semantic"
        ],
        "final_rag_usage": rag["usage"],
        "final_rag_passes_release_conditions": rag[
            "passes_release_conditions"
        ],
        "independent_review": independent_review,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", metavar="APPLICATION_ID")
    group.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        show_summary()
    else:
        show_case(args.case)


if __name__ == "__main__":
    main()
