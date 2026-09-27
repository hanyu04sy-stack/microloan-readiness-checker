"""Run and checkpoint the final rules-plus-project-RAG evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.gemini_client import GeminiStructuredClient  # noqa: E402
from microloan_checker.models import Application  # noqa: E402
from microloan_checker.rag import run_rag_hybrid  # noqa: E402
from microloan_checker.security import detect_prompt_injection  # noqa: E402


MODEL = "gemini-3.8-flash"
TOP_K = 3
INPUT_PRICE_PER_MILLION_USD = 0.75
OUTPUT_PRICE_PER_MILLION_USD = 3.75
RESULTS_ROOT = PROJECT_ROOT / "results"
CHECKPOINT_PATH = RESULTS_ROOT / "rag_live_checkpoint.json"
FINAL_PATH = RESULTS_ROOT / "rag_final_test.json"
TRANSIENT_LOG_PATH = RESULTS_ROOT / "rag_transient_attempts.json"
MANIFEST_PATH = PROJECT_ROOT / "data" / "final_test" / "rag_evaluation_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise RuntimeError("Freeze the RAG evaluation manifest before running")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("model") != MODEL or manifest.get("top_k") != TOP_K:
        raise RuntimeError("RAG manifest model or top_k does not match the evaluator")
    changed = []
    for relative, expected in manifest.get("files", {}).items():
        path = PROJECT_ROOT / relative
        actual = _sha256(path) if path.is_file() else "missing"
        if actual != expected:
            changed.append(relative)
    if changed:
        raise RuntimeError(f"Frozen RAG evaluation inputs changed: {changed}")
    return manifest


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
    expected_reviews = sum(row["expected_manual_review"] for row in predictions)
    predicted_reviews = sum(
        "Manual Review" in row["predicted_outputs"] for row in predictions
    )
    correct_reviews = sum(
        row["expected_manual_review"]
        and "Manual Review" in row["predicted_outputs"]
        for row in predictions
    )
    clean_cases = sum(not row["actual_flag_worthy"] for row in predictions)
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
            correct_reviews / expected_reviews if expected_reviews else None
        ),
        "unnecessary_review_rate": (
            unnecessary_reviews / clean_cases if clean_cases else None
        ),
    }


def _citation_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [
        row
        for row in predictions
        if row["result"]["semantic_result"]["status"] == "success"
    ]
    sent_to_retrieval = [
        row
        for row in predictions
        if not row["result"]["security"]["prompt_injection_detected"]
    ]
    retrieved = [
        row
        for row in sent_to_retrieval
        if row["result"]["retrieval"]["retrieved_chunks"]
    ]
    responses_with_citations = 0
    valid_citations = 0
    total_citations = 0
    for row in successful:
        retrieval = row["result"]["retrieval"]
        cited = retrieval["cited_chunk_ids"]
        if cited:
            responses_with_citations += 1
        allowed = {item["chunk_id"] for item in retrieval["retrieved_chunks"]}
        total_citations += len(cited)
        valid_citations += sum(item in allowed for item in cited)
    return {
        "successful_rag_responses": len(successful),
        "responses_with_citations": responses_with_citations,
        "citation_coverage": (
            responses_with_citations / len(successful) if successful else None
        ),
        "valid_citations": valid_citations,
        "total_citations": total_citations,
        "citation_validity": (
            valid_citations / total_citations if total_citations else None
        ),
        "cases_sent_to_retrieval": len(sent_to_retrieval),
        "cases_with_retrieved_context": len(retrieved),
        "retrieval_coverage": (
            len(retrieved) / len(sent_to_retrieval) if sent_to_retrieval else None
        ),
        "semantic_support_review": "pending_independent_manual_audit",
    }


def _security_suite_metrics() -> dict[str, Any]:
    records = _read_jsonl(
        PROJECT_ROOT / "data" / "security" / "prompt_injection_cases.jsonl"
    )
    malicious = [row for row in records if row["expected_detection"]]
    benign = [row for row in records if not row["expected_detection"]]
    blocked = sum(bool(detect_prompt_injection(row["text"])) for row in malicious)
    passed = sum(not detect_prompt_injection(row["text"]) for row in benign)
    return {
        "malicious_cases": len(malicious),
        "malicious_cases_blocked": blocked,
        "malicious_suite_block_rate": blocked / len(malicious) if malicious else None,
        "benign_cases": len(benign),
        "benign_cases_passed": passed,
        "benign_suite_pass_rate": passed / len(benign) if benign else None,
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
    if payload.get("model") != MODEL or payload.get("top_k") != TOP_K:
        raise RuntimeError("RAG checkpoint configuration does not match evaluator")
    rows = payload.get("predictions", [])
    quota_attempts = [row for row in rows if _is_quota_failure(row)]
    finalized = [row for row in rows if not _is_quota_failure(row)]
    transient = []
    if TRANSIENT_LOG_PATH.exists():
        transient = json.loads(
            TRANSIENT_LOG_PATH.read_text(encoding="utf-8")
        ).get("attempts", [])
    known = {
        (row["application_id"], row["result"]["semantic_result"]["error"])
        for row in transient
    }
    for row in quota_attempts:
        key = (row["application_id"], row["result"]["semantic_result"]["error"])
        if key not in known:
            transient.append(row)
            known.add(key)
    if quota_attempts:
        _write_json(
            TRANSIENT_LOG_PATH,
            {"model": MODEL, "top_k": TOP_K, "attempts": transient},
        )
        _write_json(
            CHECKPOINT_PATH,
            {
                "model": MODEL,
                "top_k": TOP_K,
                "predictions": finalized,
                "completed": len(finalized),
            },
        )
    return finalized, transient


def evaluate(
    *,
    max_new_cases: int | None = None,
    delay_seconds: float = 0.0,
) -> dict[str, Any]:
    manifest = _verify_manifest()
    root = PROJECT_ROOT / "data" / "final_test"
    applications = _read_jsonl(root / "applications.jsonl")
    labels = {
        row["application_id"]: row
        for row in _read_jsonl(root / "labels.jsonl")
    }
    predictions, transient_attempts = _load_checkpoint()
    completed_ids = {row["application_id"] for row in predictions}
    client = GeminiStructuredClient(model=MODEL, max_attempts=3)
    new_finalized = 0
    next_delay = 0.0

    for record in applications:
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
        result = run_rag_hybrid(
            Application.from_mapping(record),
            client,
            knowledge_root=PROJECT_ROOT / "knowledge_base",
            top_k=TOP_K,
        )
        result_payload = result.to_dict()
        label = labels[application_id]
        prediction = {
            "application_id": application_id,
            "eval_slice": label["eval_slice"],
            "actual_flag_worthy": label["flag_worthy"],
            "expected_outputs": label["expected_outputs"],
            "expected_manual_review": label["expected_manual_review"],
            "predicted_flag_worthy": result.hybrid_result.flag_worthy,
            "predicted_outputs": [
                item.value for item in result.hybrid_result.outputs
            ],
            "result": result_payload,
        }
        if _is_quota_failure(prediction):
            transient_attempts.append(prediction)
            _write_json(
                TRANSIENT_LOG_PATH,
                {"model": MODEL, "top_k": TOP_K, "attempts": transient_attempts},
            )
            _write_json(
                CHECKPOINT_PATH,
                {
                    "model": MODEL,
                    "top_k": TOP_K,
                    "predictions": predictions,
                    "completed": len(predictions),
                },
            )
            print(
                f"quota_pause application={application_id} "
                f"completed={len(predictions)}/50",
                flush=True,
            )
            break
        predictions.append(prediction)
        new_finalized += 1
        _write_json(
            CHECKPOINT_PATH,
            {
                "model": MODEL,
                "top_k": TOP_K,
                "predictions": predictions,
                "completed": len(predictions),
            },
        )
        status = result_payload["semantic_result"]["status"]
        print(
            f"[{len(predictions):02d}/50] {application_id} "
            f"semantic_status={status}",
            flush=True,
        )
        error = result_payload["semantic_result"].get("error") or ""
        next_delay = max(delay_seconds, 45.0 if "503" in error else 0.0)

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
    prompt_tokens = sum(call["prompt_tokens"] or 0 for call in calls)
    output_tokens = sum(call["output_tokens"] or 0 for call in calls)
    total_tokens = sum(call["total_tokens"] or 0 for call in calls)
    estimated_non_input_tokens = max(total_tokens - prompt_tokens, 0)
    attributable_cost = (
        prompt_tokens / 1_000_000 * INPUT_PRICE_PER_MILLION_USD
        + estimated_non_input_tokens
        / 1_000_000
        * OUTPUT_PRICE_PER_MILLION_USD
    )
    citation_metrics = _citation_metrics(predictions)
    security_metrics = _security_suite_metrics()
    report = {
        "evaluation_status": "complete" if len(predictions) == 50 else "incomplete",
        "system": "rules_plus_project_rag_plus_llm",
        "model": MODEL,
        "top_k": TOP_K,
        "manifest": {
            "path": str(MANIFEST_PATH.relative_to(PROJECT_ROOT)),
            "status": manifest["status"],
            "dataset_limitation": manifest["dataset_limitation"],
        },
        "release_conditions": manifest["release_conditions"],
        "metrics": {name: _metric_rows(rows) for name, rows in slices.items()},
        "retrieval_and_citations": citation_metrics,
        "security_suite": security_metrics,
        "usage": {
            "successful_model_calls": len(calls),
            "semantic_failures": len(predictions) - len(calls),
            "total_attempts_for_successful_calls": sum(
                call["attempt_count"] for call in calls
            ),
            "retry_count_for_successful_calls": sum(
                call["attempt_count"] - 1 for call in calls
            ),
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_output_plus_thinking_tokens": estimated_non_input_tokens,
            "total_latency_ms": sum(call["latency_ms"] or 0 for call in calls),
        },
        "cost": {
            "pricing_date": "2026-09-27",
            "input_usd_per_million_tokens": INPUT_PRICE_PER_MILLION_USD,
            "output_and_thinking_usd_per_million_tokens": OUTPUT_PRICE_PER_MILLION_USD,
            "attributable_direct_model_cost_usd": attributable_cost,
            "failed_attempt_cost_note": (
                "No cost is invented for failed attempts without usage metadata."
            ),
        },
        "predictions": predictions,
    }
    full = report["metrics"]["full_test"]
    conditions = report["release_conditions"]
    report["passes_release_conditions"] = (
        len(predictions) == 50
        and full["precision"] is not None
        and full["recall"] is not None
        and full["precision"] >= conditions["precision_minimum"]
        and full["recall"] >= conditions["recall_minimum"]
        and citation_metrics["citation_coverage"]
        >= conditions["citation_coverage_minimum"]
        and citation_metrics["citation_validity"]
        >= conditions["citation_validity_minimum"]
        and security_metrics["malicious_suite_block_rate"]
        >= conditions["malicious_suite_block_rate_minimum"]
        and security_metrics["benign_suite_pass_rate"]
        >= conditions["benign_suite_pass_rate_minimum"]
    )
    if len(predictions) == 50:
        _write_json(FINAL_PATH, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new-cases", type=int, default=None)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify frozen hashes and the offline security suite without an API call",
    )
    args = parser.parse_args()
    if args.verify_only:
        verified = _verify_manifest()
        print(
            json.dumps(
                {
                    "manifest_status": verified["status"],
                    "frozen_files": len(verified["files"]),
                    "security_suite": _security_suite_metrics(),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(0)
    result = evaluate(
        max_new_cases=args.max_new_cases,
        delay_seconds=args.delay_seconds,
    )
    print(
        json.dumps(
            {
                "metrics": result["metrics"],
                "retrieval_and_citations": result["retrieval_and_citations"],
                "security_suite": result["security_suite"],
                "usage": result["usage"],
                "cost": result["cost"],
                "passes_release_conditions": result["passes_release_conditions"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
