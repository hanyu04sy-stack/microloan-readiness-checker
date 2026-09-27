"""Evaluate the deterministic baseline on the frozen final test set."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.models import Application  # noqa: E402
from microloan_checker.rules import run_rule_baseline  # noqa: E402


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    for row in rows:
        actual = row["actual_flag_worthy"]
        predicted = row["predicted_flag_worthy"]
        if actual and predicted:
            counts["true_positive"] += 1
        elif not actual and predicted:
            counts["false_positive"] += 1
        elif not actual and not predicted:
            counts["true_negative"] += 1
        else:
            counts["false_negative"] += 1

    tp = counts["true_positive"]
    fp = counts["false_positive"]
    fn = counts["false_negative"]
    precision = tp / (tp + fp) if tp + fp else None
    recall = _safe_divide(tp, tp + fn)
    return {
        **{name: counts[name] for name in (
            "true_positive",
            "false_positive",
            "true_negative",
            "false_negative",
        )},
        "precision": precision,
        "recall": recall,
        "f1": (
            _safe_divide(2 * precision * recall, precision + recall)
            if precision is not None
            else 0.0
        ),
        "manual_review_rate": _safe_divide(
            sum("Manual Review" in row["predicted_outputs"] for row in rows),
            len(rows),
        ),
    }


def evaluate() -> dict[str, Any]:
    root = PROJECT_ROOT / "data" / "final_test"
    applications = _read_jsonl(root / "applications.jsonl")
    labels = {
        row["application_id"]: row for row in _read_jsonl(root / "labels.jsonl")
    }
    predictions = []
    for record in applications:
        result = run_rule_baseline(Application.from_mapping(record))
        label = labels[result.application_id]
        predictions.append(
            {
                "application_id": result.application_id,
                "eval_slice": label["eval_slice"],
                "actual_flag_worthy": label["flag_worthy"],
                "expected_outputs": label["expected_outputs"],
                "predicted_flag_worthy": result.flag_worthy,
                "predicted_outputs": [item.value for item in result.outputs],
                "predicted_issue_codes": [
                    issue.code for issue in result.issues
                ],
            }
        )

    slices = {
        "full_test": predictions,
        "handwritten_semantic": [
            row
            for row in predictions
            if row["eval_slice"] == "handwritten_semantic_contradiction"
        ],
        "deterministic": [
            row
            for row in predictions
            if row["eval_slice"]
            in {"missing_document", "numeric_or_field_contradiction"}
        ],
        "ambiguous_purpose": [
            row for row in predictions if row["eval_slice"] == "ambiguous_purpose"
        ],
    }
    report = {
        "system": "rule_only_baseline",
        "release_conditions": {"precision_minimum": 0.70, "recall_minimum": 0.90},
        "metrics": {name: _metrics(rows) for name, rows in slices.items()},
        "predictions": predictions,
    }
    full = report["metrics"]["full_test"]
    report["passes_release_conditions"] = (
        full["precision"] is not None
        and full["precision"] >= 0.70
        and full["recall"] >= 0.90
    )
    return report


if __name__ == "__main__":
    report = evaluate()
    output = PROJECT_ROOT / "results" / "rule_only_final_test.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2, sort_keys=True))
