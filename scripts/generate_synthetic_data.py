"""Generate the confirmed synthetic development, validation, and scripted test data.

The 15 instructor-required student-authored semantic test cases are not generated
here. This script creates only their authoring template when it does not exist.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"
GENERATOR_VERSION = 2
RANDOM_SEED = 6201

PURPOSE_TEXT = {
    "MEDICAL_EXPENSE": "Payment for a scheduled medical treatment.",
    "EDUCATION": "Payment for a professional course fee.",
    "HOME_REPAIR": "Repairing water damage in my residence.",
    "SMALL_BUSINESS": "Purchasing inventory for a small retail business.",
    "VEHICLE": "Repairing a vehicle used for daily transport.",
    "DEBT_CONSOLIDATION": "Combining existing personal debts into one repayment.",
    "OTHER": "Replacing essential household appliances after a breakdown.",
}

VAGUE_PURPOSE_TEXT = (
    "For personal needs.",
    "For an important expense.",
    "To cover several things.",
    "For something urgent.",
    "For general use.",
)

APPLICATION_FIELDS = (
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
)


@dataclass
class Case:
    application: dict[str, Any]
    label: dict[str, Any]


def _base_application(ordinal: int) -> dict[str, Any]:
    categories = tuple(PURPOSE_TEXT)
    category = categories[ordinal % len(categories)]
    income = 3000 + (ordinal % 9) * 250
    return {
        "declared_monthly_income": income,
        "income_proof_monthly_income": income,
        "bank_statement_average_monthly_inflow": income,
        "requested_loan_amount": 4000 + (ordinal % 8) * 1000,
        "existing_monthly_liabilities": (ordinal % 6) * 100,
        "loan_purpose_category": category,
        "loan_purpose_text": PURPOSE_TEXT[category],
        "identity_proof_present": True,
        "income_proof_present": True,
        "bank_statement_present": True,
    }


def _label(
    *,
    issue_codes: list[str],
    outputs: list[str],
    manual_review: bool,
    rationale: str,
    evidence_fields: list[str],
    case_source: str = "generated",
    label_status: str = "draft",
    eval_slice: str,
) -> dict[str, Any]:
    return {
        "expected_issue_codes": issue_codes,
        "expected_outputs": outputs,
        "flag_worthy": outputs != ["Complete"],
        "expected_manual_review": manual_review,
        "label_rationale": rationale,
        "evidence_fields": evidence_fields,
        "case_source": case_source,
        "label_status": label_status,
        "eval_slice": eval_slice,
    }


def _clean_case(ordinal: int, label_status: str) -> Case:
    return Case(
        application=_base_application(ordinal),
        label=_label(
            issue_codes=[],
            outputs=["Complete"],
            manual_review=False,
            rationale="All required fields and documents are present and internally consistent.",
            evidence_fields=[],
            label_status=label_status,
            eval_slice="clean",
        ),
    )


def _missing_document_case(ordinal: int, label_status: str) -> Case:
    application = _base_application(ordinal)
    variants = (
        (
            "identity_proof_present",
            None,
            "MISSING_IDENTITY_PROOF",
            ["identity_proof_present"],
            "Identity proof is absent.",
        ),
        (
            "income_proof_present",
            "income_proof_monthly_income",
            "MISSING_INCOME_PROOF",
            ["income_proof_present"],
            "Income proof is absent.",
        ),
        (
            "bank_statement_present",
            "bank_statement_average_monthly_inflow",
            "MISSING_BANK_STATEMENT",
            ["bank_statement_present"],
            "Bank statement is absent.",
        ),
    )
    presence_field, value_field, code, evidence, rationale = variants[ordinal % 3]
    application[presence_field] = False
    if value_field is not None:
        application[value_field] = None
    return Case(
        application=application,
        label=_label(
            issue_codes=[code],
            outputs=["Missing Documents"],
            manual_review=False,
            rationale=rationale,
            evidence_fields=evidence,
            label_status=label_status,
            eval_slice="missing_document",
        ),
    )


def _numeric_case(ordinal: int, label_status: str) -> Case:
    application = _base_application(ordinal)
    variant = ordinal % 3
    if variant == 0:
        application["income_proof_monthly_income"] = (
            application["declared_monthly_income"] + 500
        )
        code = "DECLARED_INCOME_MISMATCH"
        rationale = "Declared income differs from the normalized income-proof value."
        evidence = ["declared_monthly_income", "income_proof_monthly_income"]
    elif variant == 1:
        application["bank_statement_average_monthly_inflow"] = (
            application["declared_monthly_income"] - 500
        )
        code = "BANK_INFLOW_MISMATCH"
        rationale = "Declared income differs from the normalized bank-statement inflow."
        evidence = [
            "declared_monthly_income",
            "bank_statement_average_monthly_inflow",
        ]
    else:
        application["requested_loan_amount"] = 0
        code = "INVALID_NUMERIC_VALUE"
        rationale = "The requested loan amount is not greater than zero."
        evidence = ["requested_loan_amount"]
    return Case(
        application=application,
        label=_label(
            issue_codes=[code],
            outputs=["Inconsistent Information"],
            manual_review=False,
            rationale=rationale,
            evidence_fields=evidence,
            label_status=label_status,
            eval_slice="numeric_or_field_contradiction",
        ),
    )


def _vague_case(ordinal: int, label_status: str) -> Case:
    application = _base_application(ordinal)
    application["loan_purpose_text"] = VAGUE_PURPOSE_TEXT[
        ordinal % len(VAGUE_PURPOSE_TEXT)
    ]
    return Case(
        application=application,
        label=_label(
            issue_codes=["VAGUE_LOAN_PURPOSE"],
            outputs=["Manual Review"],
            manual_review=True,
            rationale="The stated purpose does not identify a concrete use of funds.",
            evidence_fields=["loan_purpose_text"],
            label_status=label_status,
            eval_slice="ambiguous_purpose",
        ),
    )


def _generated_semantic_case(ordinal: int, label_status: str) -> Case:
    application = _base_application(ordinal)
    categories = tuple(PURPOSE_TEXT)
    stated_category = application["loan_purpose_category"]
    other_index = (categories.index(stated_category) + 1) % len(categories)
    application["loan_purpose_text"] = PURPOSE_TEXT[categories[other_index]]
    return Case(
        application=application,
        label=_label(
            issue_codes=["PURPOSE_CATEGORY_CONTRADICTION"],
            outputs=["Inconsistent Information"],
            manual_review=False,
            rationale="The free-text purpose describes a different project category.",
            evidence_fields=["loan_purpose_category", "loan_purpose_text"],
            label_status=label_status,
            eval_slice="generated_semantic_development",
        ),
    )


BUILDERS = {
    "clean": _clean_case,
    "missing_document": _missing_document_case,
    "numeric_or_field_contradiction": _numeric_case,
    "ambiguous_purpose": _vague_case,
    "generated_semantic_development": _generated_semantic_case,
}


def build_cases(
    *,
    split_name: str,
    start_index: int,
    counts: dict[str, int],
    seed: int,
    label_status: str,
) -> list[Case]:
    cases: list[Case] = []
    ordinal = 0
    for slice_name, count in counts.items():
        builder = BUILDERS[slice_name]
        for _ in range(count):
            cases.append(builder(ordinal, label_status))
            ordinal += 1

    random.Random(seed).shuffle(cases)
    for index, case in enumerate(cases, 1):
        application_id = f"APP_{start_index + index - 1:04d}"
        case.application = {"application_id": application_id, **case.application}
        case.label = {
            "application_id": application_id,
            "split": split_name,
            **case.label,
        }
    return cases


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_handwritten_template(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "application_id",
                "loan_purpose_category",
                "loan_purpose_text",
                "contradiction_rationale",
                "author_check_status",
                "independent_review_status",
                "draft_origin",
            ],
        )
        writer.writeheader()
        for index in range(286, 301):
            writer.writerow(
                {
                    "application_id": f"APP_{index:04d}",
                    "loan_purpose_category": "",
                    "loan_purpose_text": "",
                    "contradiction_rationale": "",
                    "author_check_status": "pending_user_review",
                    "independent_review_status": "not_arranged",
                    "draft_origin": "blank_template",
                }
            )


def generate() -> dict[str, Any]:
    specifications = {
        "development": {
            "start_index": 1,
            "seed": RANDOM_SEED,
            "label_status": "draft",
            "counts": {
                "clean": 80,
                "missing_document": 40,
                "numeric_or_field_contradiction": 40,
                "ambiguous_purpose": 20,
                "generated_semantic_development": 20,
            },
        },
        "validation": {
            "start_index": 201,
            "seed": RANDOM_SEED + 1,
            "label_status": "draft",
            "counts": {
                "clean": 20,
                "missing_document": 10,
                "numeric_or_field_contradiction": 10,
                "ambiguous_purpose": 5,
                "generated_semantic_development": 5,
            },
        },
        "test": {
            "start_index": 251,
            "seed": RANDOM_SEED + 2,
            "label_status": "frozen",
            "counts": {
                "clean": 20,
                "missing_document": 5,
                "numeric_or_field_contradiction": 5,
                "ambiguous_purpose": 5,
            },
        },
    }

    written_files: list[Path] = []
    summary: dict[str, Any] = {}
    for split_name, spec in specifications.items():
        cases = build_cases(
            split_name=split_name,
            start_index=spec["start_index"],
            counts=spec["counts"],
            seed=spec["seed"],
            label_status=spec["label_status"],
        )
        applications_path = DATA_ROOT / split_name / "applications.jsonl"
        labels_path = DATA_ROOT / split_name / "labels.jsonl"
        _write_jsonl(applications_path, (case.application for case in cases))
        _write_jsonl(labels_path, (case.label for case in cases))
        written_files.extend((applications_path, labels_path))
        summary[split_name] = {
            "generated_applications": len(cases),
            "counts": spec["counts"],
        }

    template_path = DATA_ROOT / "test" / "handwritten_semantic_template.csv"
    _ensure_handwritten_template(template_path)

    manifest = {
        "generator": "scripts/generate_synthetic_data.py",
        "generator_version": GENERATOR_VERSION,
        "random_seed": RANDOM_SEED,
        "status": "incomplete_until_15_semantic_drafts_are_personally_reviewed_and_frozen",
        "summary": summary,
        "files": {
            str(path.relative_to(PROJECT_ROOT)): _sha256(path)
            for path in written_files
        },
        "handwritten_template": str(template_path.relative_to(PROJECT_ROOT)),
        "handwritten_template_sha256": _sha256(template_path),
    }
    manifest_path = DATA_ROOT / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, ensure_ascii=False))
