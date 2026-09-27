"""Run and checkpoint the live rules-plus-Gemini final-test evaluation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.gemini_client import GeminiStructuredClient  # noqa: E402
from microloan_checker.hybrid import run_hybrid  # noqa: E402
from microloan_checker.models import Application  # noqa: E402
from microloan_checker.semantic import SemanticChecker  # noqa: E402


MODEL = "gemini-3.8-flash"
RESULTS_ROOT = PROJECT_ROOT / "results"
CHECKPOINT_PATH = RESULTS_ROOT / "hybrid_live_checkpoint.json"
FINAL_PATH = RESULTS_ROOT / "hybrid_final_test.json"
TRANSIENT_LOG_PATH = RESULTS_ROOT / "hybrid_transient_attempts.json"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _metric_rows(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    for row in predictions:
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
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else 0.0
    )
    total = len(predictions)
    actual_reviews = sum(row["expected_manual_review"] for row in predictions)
    predicted_reviews = sum(
        "Manual Review" in row["predicted_outputs"] for row in predictions
    )
    correctly_reviewed = sum(
        row["expected_manual_review"]
        and "Manual Review" in row["predicted_outputs"]
        for row in predictions
    )
    complete_cases = sum(not row["actual_flag_worthy"] for row in predictions)
    unnecessary_reviews = sum(
        not row["actual_flag_worthy"]
        and "Manual Review" in row["predicted_outputs"]
        for row in predictions
    )
    return {
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": counts["true_negative"],
        "false_negative": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "manual_review_rate": predicted_reviews / total if total else 0.0,
        "appropriate_review_capture": (
            correctly_reviewed / actual_reviews if actual_reviews else None
        ),
        "unnecessary_review_rate": (
            unnecessary_reviews / complete_cases if complete_cases else None
        ),
    }


def _is_quota_failure(row: dict[str, Any]) -> bool:
    semantic = row["result"]["semantic_result"]
    return semantic["status"] == "error" and (
        "429" in semantic["error"] or "RESOURCE_EXHAUSTED" in semantic["error"]
    )


def _load_checkpoint() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not CHECKPOINT_PATH.exists():
        return [], []
    payload = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    if payload.get("model") != MODEL:
        raise RuntimeError("Checkpoint model does not match the frozen evaluation model")
    rows = payload.get("predictions", [])
    quota_attempts = [row for row in rows if _is_quota_failure(row)]
    finalized = [row for row in rows if not _is_quota_failure(row)]
    existing_attempts = []
    if TRANSIENT_LOG_PATH.exists():
        existing_attempts = json.loads(
            TRANSIENT_LOG_PATH.read_text(encoding="utf-8")
        ).get("attempts", [])
    known = {
        (row["application_id"], row["result"]["semantic_result"]["error"])
        for row in existing_attempts
    }
    for row in quota_attempts:
        key = (row["application_id"], row["result"]["semantic_result"]["error"])
        if key not in known:
            existing_attempts.append(row)
            known.add(key)
    if quota_attempts:
        _write_json(
            TRANSIENT_LOG_PATH,
            {"model": MODEL, "attempts": existing_attempts},
        )
        _write_json(
            CHECKPOINT_PATH,
            {"model": MODEL, "predictions": finalized, "completed": len(finalized)},
        )
    return finalized, existing_attempts


def evaluate(
    *,
    max_new_cases: int | None = None,
    delay_seconds: float = 0.0,
) -> dict[str, Any]:
    root = PROJECT_ROOT / "data" / "final_test"
    applications = _read_jsonl(root / "applications.jsonl")
    labels = {
        row["application_id"]: row for row in _read_jsonl(root / "labels.jsonl")
    }
    predictions, transient_attempts = _load_checkpoint()
    completed_ids = {row["application_id"] for row in predictions}
    client = GeminiStructuredClient(model=MODEL, max_attempts=3)
    checker = SemanticChecker(client)
    new_finalized = 0
    next_delay = 0.0

    for index, record in enumerate(applications, 1):
        application_id = record["application_id"]
        if application_id in completed_ids:
            continue
        if max_new_cases is not None and new_finalized >= max_new_cases:
            print(
                f"run_limit_reached new_finalized={new_finalized} "
                f"completed={len(predictions)}/50",
                flush=True,
            )
            break
        if next_delay:
            time.sleep(next_delay)
        result = run_hybrid(Application.from_mapping(record), checker)
        result_payload = result.to_dict()
        label = labels[application_id]
        prediction = {
            "application_id": application_id,
            "eval_slice": label["eval_slice"],
            "actual_flag_worthy": label["flag_worthy"],
            "expected_outputs": label["expected_outputs"],
            "expected_manual_review": label["expected_manual_review"],
            "predicted_flag_worthy": result.flag_worthy,
            "predicted_outputs": [item.value for item in result.outputs],
            "result": result_payload,
        }
        if _is_quota_failure(prediction):
            transient_attempts.append(prediction)
            _write_json(
                TRANSIENT_LOG_PATH,
                {"model": MODEL, "attempts": transient_attempts},
            )
            _write_json(
                CHECKPOINT_PATH,
                {"model": MODEL, "predictions": predictions, "completed": len(predictions)},
            )
            print(
                f"quota_pause application={application_id} completed={len(predictions)}/50",
                flush=True,
            )
            break
        predictions.append(prediction)
        new_finalized += 1
        _write_json(
            CHECKPOINT_PATH,
            {"model": MODEL, "predictions": predictions, "completed": len(predictions)},
        )
        status = result_payload["semantic_result"]["status"]
        print(f"[{len(predictions):02d}/50] {application_id} semantic_status={status}", flush=True)
        semantic_error = result_payload["semantic_result"].get("error") or ""
        next_delay = max(delay_seconds, 45.0 if "503" in semantic_error else 0.0)

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
    calls = [
        row["result"]["model_call"]
        for row in predictions
        if row["result"]["model_call"] is not None
    ]
    report = {
        "evaluation_status": "complete" if len(predictions) == 50 else "incomplete",
        "system": "rules_plus_llm",
        "model": MODEL,
        "release_conditions": {"precision_minimum": 0.70, "recall_minimum": 0.90},
        "metrics": {name: _metric_rows(rows) for name, rows in slices.items()},
        "usage": {
            "successful_model_calls": len(calls),
            "semantic_failures": len(predictions) - len(calls),
            "total_attempts_for_successful_calls": sum(
                call["attempt_count"] for call in calls
            ),
            "retry_count_for_successful_calls": sum(
                call["attempt_count"] - 1 for call in calls
            ),
            "prompt_tokens": sum(call["prompt_tokens"] or 0 for call in calls),
            "output_tokens": sum(call["output_tokens"] or 0 for call in calls),
            "total_tokens": sum(call["total_tokens"] or 0 for call in calls),
            "total_latency_ms": sum(call["latency_ms"] or 0 for call in calls),
        },
        "predictions": predictions,
    }
    full = report["metrics"]["full_test"]
    report["passes_release_conditions"] = (
        len(predictions) == 50
        and full["precision"] is not None
        and full["recall"] is not None
        and full["precision"] >= 0.70
        and full["recall"] >= 0.90
    )
    if len(predictions) == 50:
        _write_json(FINAL_PATH, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new-cases", type=int, default=None)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    args = parser.parse_args()
    result = evaluate(
        max_new_cases=args.max_new_cases,
        delay_seconds=args.delay_seconds,
    )
    print(json.dumps({"metrics": result["metrics"], "usage": result["usage"], "passes_release_conditions": result["passes_release_conditions"]}, ensure_ascii=False, indent=2, sort_keys=True))
