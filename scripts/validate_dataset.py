"""Validate generated data counts, leakage boundaries, and deterministic labels."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from microloan_checker.models import Application  # noqa: E402
from microloan_checker.rules import run_rule_baseline  # noqa: E402


APPLICATION_KEYS = {
    "application_id",
    "declared_monthly_income",
    "income_proof_monthly_income",
    "bank_statement_average_monthly_inflow",
    "requested_loan_amount",
    "existing_monthly_liabilities",
    "loan_purpose_category",
    "loan_purpose_text",
    "identity_proof_present",
    "income_proof_present",
    "bank_statement_present",
}

EXPECTED_SPLIT_COUNTS = {"development": 200, "validation": 50, "test": 35}
EXPECTED_TEST_SLICES = {
    "clean": 20,
    "missing_document": 5,
    "numeric_or_field_contradiction": 5,
    "ambiguous_purpose": 5,
}
ALLOWED_PURPOSE_CATEGORIES = {
    "MEDICAL_EXPENSE",
    "EDUCATION",
    "HOME_REPAIR",
    "SMALL_BUSINESS",
    "VEHICLE",
    "DEBT_CONSOLIDATION",
    "OTHER",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def validate() -> dict:
    report = {
        "splits": {},
        "handwritten_completed": 0,
        "handwritten_ready": 0,
        "final_test_ready": False,
        "errors": [],
    }
    seen_ids: set[str] = set()

    for split_name, expected_count in EXPECTED_SPLIT_COUNTS.items():
        applications = read_jsonl(
            PROJECT_ROOT / "data" / split_name / "applications.jsonl"
        )
        labels = read_jsonl(PROJECT_ROOT / "data" / split_name / "labels.jsonl")
        if len(applications) != expected_count or len(labels) != expected_count:
            report["errors"].append(
                f"{split_name} count mismatch: applications={len(applications)}, labels={len(labels)}"
            )

        app_by_id = {record["application_id"]: record for record in applications}
        label_by_id = {record["application_id"]: record for record in labels}
        if set(app_by_id) != set(label_by_id):
            report["errors"].append(f"{split_name} application and label IDs differ")

        for application_id, record in app_by_id.items():
            if set(record) != APPLICATION_KEYS:
                report["errors"].append(
                    f"{application_id} has unexpected or missing application fields"
                )
            if application_id in seen_ids:
                report["errors"].append(f"Duplicate application ID: {application_id}")
            seen_ids.add(application_id)

            application = Application.from_mapping(record)
            label = label_by_id[application_id]
            rule_result = run_rule_baseline(application)
            if label["eval_slice"] in {
                "clean",
                "missing_document",
                "numeric_or_field_contradiction",
            }:
                actual_outputs = [item.value for item in rule_result.outputs]
                if actual_outputs != label["expected_outputs"]:
                    report["errors"].append(
                        f"{application_id} rule output {actual_outputs} does not match label {label['expected_outputs']}"
                    )
            elif label["eval_slice"] in {
                "ambiguous_purpose",
                "generated_semantic_development",
            }:
                if [item.value for item in rule_result.outputs] != ["Complete"]:
                    report["errors"].append(
                        f"{application_id} semantic slice unexpectedly triggers deterministic rules"
                    )

        slices = Counter(record["eval_slice"] for record in labels)
        report["splits"][split_name] = {
            "applications": len(applications),
            "slices": dict(sorted(slices.items())),
        }
        if split_name == "test" and dict(slices) != EXPECTED_TEST_SLICES:
            report["errors"].append(
                f"Test slice composition differs: {dict(slices)}"
            )

    template_path = PROJECT_ROOT / "data" / "test" / "handwritten_semantic_template.csv"
    with template_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 15:
        report["errors"].append(f"Handwritten template has {len(rows)} rows, expected 15")
    expected_ids = {f"APP_{index:04d}" for index in range(286, 301)}
    if {row["application_id"] for row in rows} != expected_ids:
        report["errors"].append("Handwritten template IDs are not APP_0286 through APP_0300")
    for row in rows:
        application_id = row["application_id"]
        if row["loan_purpose_category"] not in ALLOWED_PURPOSE_CATEGORIES:
            report["errors"].append(
                f"{application_id} has an unsupported loan purpose category"
            )
        if row.get("draft_origin") != "ai_assisted_translation_and_revision":
            report["errors"].append(
                f"{application_id} does not record the AI-assisted draft origin"
            )
    report["handwritten_completed"] = sum(
        bool(row["loan_purpose_category"].strip())
        and bool(row["loan_purpose_text"].strip())
        and bool(row["contradiction_rationale"].strip())
        for row in rows
    )
    report["handwritten_ready"] = sum(
        row["author_check_status"].strip() == "ready" for row in rows
    )
    report["final_test_ready"] = (
        report["handwritten_completed"] == 15
        and report["handwritten_ready"] == 15
    )

    report["valid"] = not report["errors"]
    return report


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["valid"] else 1)
