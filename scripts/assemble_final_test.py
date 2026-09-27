"""Assemble and freeze the confirmed 50-case final evaluation set."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"
SCRIPTED_TEST_ROOT = DATA_ROOT / "test"
FINAL_TEST_ROOT = DATA_ROOT / "final_test"
ALLOWED_PURPOSE_CATEGORIES = {
    "MEDICAL_EXPENSE",
    "EDUCATION",
    "HOME_REPAIR",
    "SMALL_BUSINESS",
    "VEHICLE",
    "DEBT_CONSOLIDATION",
    "OTHER",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_application(row: dict[str, str]) -> dict[str, Any]:
    """Use neutral, internally consistent synthetic values around the purpose fields."""

    return {
        "application_id": row["application_id"],
        "declared_monthly_income": 4000,
        "income_proof_monthly_income": 4000,
        "bank_statement_average_monthly_inflow": 4000,
        "requested_loan_amount": 6000,
        "existing_monthly_liabilities": 300,
        "loan_purpose_category": row["loan_purpose_category"],
        "loan_purpose_text": row["loan_purpose_text"],
        "identity_proof_present": True,
        "income_proof_present": True,
        "bank_statement_present": True,
    }


def _semantic_label(row: dict[str, str]) -> dict[str, Any]:
    return {
        "application_id": row["application_id"],
        "split": "final_test",
        "expected_issue_codes": ["PURPOSE_CATEGORY_CONTRADICTION"],
        "expected_outputs": ["Inconsistent Information"],
        "flag_worthy": True,
        "expected_manual_review": False,
        "label_rationale": row["contradiction_rationale"],
        "evidence_fields": ["loan_purpose_category", "loan_purpose_text"],
        "case_source": "handwritten_semantic",
        "label_status": "frozen",
        "eval_slice": "handwritten_semantic_contradiction",
    }


def build_final_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    applications = _read_jsonl(SCRIPTED_TEST_ROOT / "applications.jsonl")
    labels = _read_jsonl(SCRIPTED_TEST_ROOT / "labels.jsonl")

    template_path = SCRIPTED_TEST_ROOT / "handwritten_semantic_template.csv"
    with template_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    if len(rows) != 15:
        raise ValueError(f"Expected 15 semantic cases, found {len(rows)}")
    for row in rows:
        application_id = row["application_id"]
        if row["author_check_status"] != "ready":
            raise ValueError(f"{application_id} is not ready for freezing")
        if row["loan_purpose_category"] not in ALLOWED_PURPOSE_CATEGORIES:
            raise ValueError(f"{application_id} uses an unsupported purpose category")
        if not row["loan_purpose_text"].strip() or not row[
            "contradiction_rationale"
        ].strip():
            raise ValueError(f"{application_id} has incomplete semantic content")

    applications.extend(_semantic_application(row) for row in rows)
    labels.extend(_semantic_label(row) for row in rows)
    for label in labels:
        label["split"] = "final_test"
        label["label_status"] = "frozen"

    applications.sort(key=lambda record: record["application_id"])
    labels.sort(key=lambda record: record["application_id"])
    application_ids = [record["application_id"] for record in applications]
    label_ids = [record["application_id"] for record in labels]
    expected_ids = [f"APP_{index:04d}" for index in range(251, 301)]
    if application_ids != expected_ids or label_ids != expected_ids:
        raise ValueError("Final test IDs must be APP_0251 through APP_0300")
    return applications, labels


def assemble() -> dict[str, Any]:
    applications, labels = build_final_records()
    applications_path = FINAL_TEST_ROOT / "applications.jsonl"
    labels_path = FINAL_TEST_ROOT / "labels.jsonl"
    _write_jsonl(applications_path, applications)
    _write_jsonl(labels_path, labels)

    frozen_inputs = {
        "rules.py": PROJECT_ROOT / "src" / "microloan_checker" / "rules.py",
        "semantic.py": PROJECT_ROOT / "src" / "microloan_checker" / "semantic.py",
        "gemini_client.py": PROJECT_ROOT / "src" / "microloan_checker" / "gemini_client.py",
        "handwritten_semantic_template.csv": SCRIPTED_TEST_ROOT
        / "handwritten_semantic_template.csv",
    }
    manifest = {
        "status": "frozen",
        "applications": len(applications),
        "id_range": ["APP_0251", "APP_0300"],
        "slice_counts": {
            "clean": 20,
            "missing_document": 5,
            "numeric_or_field_contradiction": 5,
            "ambiguous_purpose": 5,
            "handwritten_semantic_contradiction": 15,
        },
        "provenance_note": (
            "APP_0286 through APP_0300 originated as student-supplied Chinese "
            "scenarios and were translated and revised in English with AI assistance."
        ),
        "independent_review_status": "not_arranged",
        "hybrid_model": "gemini-3.8-flash",
        "model_change_note": (
            "The proposal named Gemini 2.5 Flash. The live API reported that it "
            "was unavailable to new users and recommended Gemini 3.8 Flash; the "
            "student approved the replacement on 27 September 2026."
        ),
        "files": {
            "applications.jsonl": _sha256(applications_path),
            "labels.jsonl": _sha256(labels_path),
        },
        "frozen_input_hashes": {
            name: _sha256(path) for name, path in frozen_inputs.items()
        },
    }
    manifest_path = FINAL_TEST_ROOT / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(assemble(), ensure_ascii=False, indent=2, sort_keys=True))
