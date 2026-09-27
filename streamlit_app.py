"""Streamlit interface for the microloan readiness checker.

This presentation layer collects one application and calls the existing tested
rule-only or rules-plus-Gemini path. It never performs a credit decision and
never reads evaluation labels.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from microloan_checker.gemini_client import GeminiStructuredClient
from microloan_checker.hybrid import run_hybrid
from microloan_checker.models import (
    Application,
    DataValidationError,
    PurposeCategory,
    UserOutput,
)
from microloan_checker.rules import run_rule_baseline
from microloan_checker.semantic import SemanticChecker


PROJECT_ROOT = Path(__file__).resolve().parent
FINAL_APPLICATIONS = PROJECT_ROOT / "data" / "final_test" / "applications.jsonl"
DEFAULT_MODEL = "gemini-3.8-flash"


def parse_optional_number(raw_value: str, field_name: str) -> float | int | None:
    """Convert an optional text field to a number."""

    value = raw_value.strip().replace(",", "")
    if not value:
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise DataValidationError(f"{field_name} must be a number or blank") from exc
    return int(number) if number.is_integer() else number


def load_application(application_id: str) -> dict[str, Any]:
    """Load one application input; ground-truth labels are never opened."""

    with FINAL_APPLICATIONS.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("application_id") == application_id:
                return record
    raise LookupError(f"Application not found: {application_id}")


def build_record(values: dict[str, Any]) -> dict[str, Any]:
    """Build the exact application mapping consumed by the current system."""

    return {
        "application_id": values["application_id"].strip(),
        "declared_monthly_income": parse_optional_number(
            values["declared_monthly_income"], "declared_monthly_income"
        ),
        "income_proof_monthly_income": parse_optional_number(
            values["income_proof_monthly_income"], "income_proof_monthly_income"
        ),
        "bank_statement_average_monthly_inflow": parse_optional_number(
            values["bank_statement_average_monthly_inflow"],
            "bank_statement_average_monthly_inflow",
        ),
        "requested_loan_amount": parse_optional_number(
            values["requested_loan_amount"], "requested_loan_amount"
        ),
        "existing_monthly_liabilities": parse_optional_number(
            values["existing_monthly_liabilities"],
            "existing_monthly_liabilities",
        ),
        "loan_purpose_category": values["loan_purpose_category"],
        "loan_purpose_text": values["loan_purpose_text"],
        "identity_proof_present": values["identity_proof_present"],
        "income_proof_present": values["income_proof_present"],
        "bank_statement_present": values["bank_statement_present"],
    }


def _text_number(value: Any) -> str:
    return "" if value is None else str(value)


def _show_outputs(st: Any, outputs: list[str]) -> None:
    message = " · ".join(outputs)
    if outputs == [UserOutput.COMPLETE.value]:
        st.success(f"Readiness result: {message}")
    elif UserOutput.MANUAL_REVIEW.value in outputs:
        st.warning(f"Readiness result: {message}")
    else:
        st.error(f"Readiness result: {message}")


def _show_rule_issues(st: Any, issues: list[dict[str, Any]]) -> None:
    st.subheader("Deterministic findings")
    if not issues:
        st.info("No deterministic document, required-field, or numeric issue was found.")
        return
    for issue in issues:
        st.markdown(f"**{issue['code']} — {issue['output']}**")
        st.write(issue["reason"])
        st.caption("Evidence: " + ", ".join(issue["evidence_fields"]))


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="Microloan Readiness Checker",
        page_icon="✓",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container {max-width: 1120px; padding-top: 2rem;}
        [data-testid="stMetricValue"] {font-size: 1.25rem;}
        .boundary {padding: .85rem 1rem; border-radius: .6rem;
          border: 1px solid #d7dde5; background: #f7f9fc; margin-bottom: 1.25rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Microloan Application Readiness Checker")
    st.caption("PE6201 coursework prototype · one application · reversible pre-check")
    st.markdown(
        """
        <div class="boundary"><strong>Scope boundary:</strong> this tool checks whether
        application materials are complete or internally consistent. It does not score
        credit, assess affordability, approve or reject a loan, or set loan terms.</div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Check configuration")
        mode = st.radio(
            "Method",
            ["Rule-only baseline", "Rules + Gemini"],
            help="The hybrid option makes one live structured Gemini call after submission.",
        )
        model = st.text_input(
            "Gemini model",
            value=DEFAULT_MODEL,
            disabled=mode == "Rule-only baseline",
        )
        key_ready = bool(os.environ.get("GEMINI_API_KEY"))
        if mode == "Rules + Gemini":
            if key_ready:
                st.success("GEMINI_API_KEY is available")
            else:
                st.warning("GEMINI_API_KEY is not available in this process")
        st.divider()
        source = st.selectbox(
            "Input source",
            ["Sample complete application", "APP_0286", "APP_0264", "Custom"],
            help="Examples load application inputs only. Ground-truth labels are not read.",
        )
        st.caption("Gemini runs only after you click Run readiness check.")

    if source == "Sample complete application":
        defaults = json.loads(
            (PROJECT_ROOT / "data" / "sample" / "complete_application.json").read_text(
                encoding="utf-8"
            )
        )
    elif source == "Custom":
        defaults = {
            "application_id": "APP-DEMO",
            "declared_monthly_income": 4000,
            "income_proof_monthly_income": 4000,
            "bank_statement_average_monthly_inflow": 4000,
            "requested_loan_amount": 8000,
            "existing_monthly_liabilities": 500,
            "loan_purpose_category": PurposeCategory.EDUCATION.value,
            "loan_purpose_text": "Payment for a professional course fee.",
            "identity_proof_present": True,
            "income_proof_present": True,
            "bank_statement_present": True,
        }
    else:
        defaults = load_application(source)

    key_prefix = source.replace(" ", "_")
    with st.form("readiness_form"):
        st.subheader("Application input")
        left, right = st.columns([1, 1])
        with left:
            application_id = st.text_input(
                "Application ID",
                value=defaults["application_id"],
                key=f"{key_prefix}_application_id",
            )
            category_values = [item.value for item in PurposeCategory]
            default_category = defaults.get("loan_purpose_category")
            category_index = (
                category_values.index(default_category)
                if default_category in category_values
                else 0
            )
            loan_purpose_category = st.selectbox(
                "Loan purpose category",
                category_values,
                index=category_index,
                key=f"{key_prefix}_category",
            )
            loan_purpose_text = st.text_area(
                "Loan purpose text",
                value=defaults.get("loan_purpose_text") or "",
                height=145,
                key=f"{key_prefix}_purpose",
            )
        with right:
            declared_monthly_income = st.text_input(
                "Declared monthly income",
                value=_text_number(defaults.get("declared_monthly_income")),
                key=f"{key_prefix}_declared_income",
            )
            income_proof_monthly_income = st.text_input(
                "Income-proof monthly income (blank if absent)",
                value=_text_number(defaults.get("income_proof_monthly_income")),
                key=f"{key_prefix}_proof_income",
            )
            bank_statement_average_monthly_inflow = st.text_input(
                "Bank-statement average monthly inflow (blank if absent)",
                value=_text_number(defaults.get("bank_statement_average_monthly_inflow")),
                key=f"{key_prefix}_bank_inflow",
            )
            requested_loan_amount = st.text_input(
                "Requested loan amount",
                value=_text_number(defaults.get("requested_loan_amount")),
                key=f"{key_prefix}_loan_amount",
            )
            existing_monthly_liabilities = st.text_input(
                "Existing monthly liabilities",
                value=_text_number(defaults.get("existing_monthly_liabilities")),
                key=f"{key_prefix}_liabilities",
            )

        st.subheader("Document presence")
        doc1, doc2, doc3 = st.columns(3)
        with doc1:
            identity_proof_present = st.checkbox(
                "Identity proof",
                value=defaults.get("identity_proof_present", True),
                key=f"{key_prefix}_identity",
            )
        with doc2:
            income_proof_present = st.checkbox(
                "Income proof",
                value=defaults.get("income_proof_present", True),
                key=f"{key_prefix}_income_proof",
            )
        with doc3:
            bank_statement_present = st.checkbox(
                "Bank statement",
                value=defaults.get("bank_statement_present", True),
                key=f"{key_prefix}_bank_statement",
            )

        submitted = st.form_submit_button(
            "Run readiness check", type="primary", use_container_width=True
        )

    if not submitted:
        st.info("Complete or load one application, then run the readiness check.")
        return

    values = {
        "application_id": application_id,
        "declared_monthly_income": declared_monthly_income,
        "income_proof_monthly_income": income_proof_monthly_income,
        "bank_statement_average_monthly_inflow": bank_statement_average_monthly_inflow,
        "requested_loan_amount": requested_loan_amount,
        "existing_monthly_liabilities": existing_monthly_liabilities,
        "loan_purpose_category": loan_purpose_category,
        "loan_purpose_text": loan_purpose_text,
        "identity_proof_present": identity_proof_present,
        "income_proof_present": income_proof_present,
        "bank_statement_present": bank_statement_present,
    }

    try:
        application = Application.from_mapping(build_record(values))
        if mode == "Rule-only baseline":
            result = run_rule_baseline(application).to_dict()
        else:
            if not key_ready:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured. Start Streamlit from a shell "
                    "that has loaded the key."
                )
            with st.spinner("Running deterministic checks and one Gemini semantic check..."):
                client = GeminiStructuredClient(model=model.strip() or DEFAULT_MODEL)
                result = run_hybrid(application, SemanticChecker(client)).to_dict()
    except (DataValidationError, RuntimeError) as exc:
        st.error(f"The check could not run: {exc}")
        return

    st.divider()
    st.subheader("Readiness result")
    _show_outputs(st, result["outputs"])
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Application", result["application_id"])
    metric2.metric("Method", result["system"])
    metric3.metric("Requires attention", "Yes" if result["flag_worthy"] else "No")

    rule_payload = result if result["system"] == "rule_only_baseline" else result["rule_result"]
    _show_rule_issues(st, rule_payload["issues"])

    if result["system"] == "rules_plus_llm":
        st.subheader("Semantic finding")
        semantic = result["semantic_result"]
        if semantic["status"] == "success":
            st.write(semantic["reason"])
            st.write(
                "Issue codes:",
                ", ".join(semantic["semantic_issue_codes"]) or "None",
            )
            st.caption(
                "Evidence: " + (", ".join(semantic["evidence_fields"]) or "None")
            )
        else:
            st.warning("The semantic check failed safely and was routed to Manual Review.")
            st.code(semantic["error"], language=None)

        call = result.get("model_call")
        if call:
            st.subheader("Model-call record")
            cols = st.columns(4)
            cols[0].metric("Model", call["model"])
            cols[1].metric("Attempts", call["attempt_count"])
            cols[2].metric("Total tokens", call["total_tokens"] or "n/a")
            latency = call["latency_ms"]
            cols[3].metric("Latency", f"{latency / 1000:.2f}s" if latency else "n/a")

    with st.expander("Structured audit output"):
        st.json(result)
    st.caption(
        "A Credit Operations Officer must review the evidence before formal credit "
        "assessment and may override this readiness label with a recorded reason."
    )


if __name__ == "__main__":
    main()
