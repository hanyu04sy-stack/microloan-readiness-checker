"""Streamlit interface for the microloan readiness checker.

This presentation layer collects one application and calls the existing tested
rule-only or rules-plus-Gemini path. It never performs a credit decision and
never reads evaluation labels.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    # Keep the app runnable from this non-ASCII workspace path even when an
    # editable-install .pth entry is not loaded by the local Python runtime.
    sys.path.insert(0, str(SRC_ROOT))

from microloan_checker.gemini_client import GeminiStructuredClient
from microloan_checker.hybrid import run_hybrid
from microloan_checker.models import (
    Application,
    DataValidationError,
    PurposeCategory,
    UserOutput,
)
from microloan_checker.rag import run_rag_hybrid
from microloan_checker.rules import run_rule_baseline
from microloan_checker.semantic import SemanticChecker


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
        tone = "complete"
        eyebrow = "READY FOR THE NEXT CHECKPOINT"
        detail = "No readiness issue was found by the selected method."
    elif UserOutput.MANUAL_REVIEW.value in outputs:
        tone = "review"
        eyebrow = "HUMAN REVIEW REQUIRED"
        detail = "Review the evidence below before formal credit assessment."
    else:
        tone = "issue"
        eyebrow = "READINESS ISSUE DETECTED"
        detail = "The application should not move forward without correction or review."
    st.markdown(
        f"""
        <div class="result-card {tone}">
          <div class="result-eyebrow">{eyebrow}</div>
          <div class="result-title">{message}</div>
          <div class="result-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        :root {
          --ink: #102A43;
          --muted: #627D98;
          --teal: #0F766E;
          --navy: #102A43;
          --line: #D9E2EC;
          --surface: #FFFFFF;
        }
        .stApp {background: linear-gradient(180deg, #F5F8FC 0%, #EDF4F5 100%);}
        .block-container {max-width: 1160px; padding-top: 1.8rem; padding-bottom: 4rem;}
        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, #102A43 0%, #163E55 100%);
          border-right: 0;
        }
        [data-testid="stSidebar"] * {color: #F5FAFC;}
        [data-testid="stSidebar"] [data-baseweb="radio"] > div,
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {color: #102A43;}
        [data-testid="stSidebar"] hr {border-color: rgba(255,255,255,.18);}
        [data-testid="stForm"] {
          background: rgba(255,255,255,.94);
          border: 1px solid rgba(159,179,200,.48);
          border-radius: 20px;
          padding: 1.35rem 1.55rem 1.55rem;
          box-shadow: 0 16px 46px rgba(16,42,67,.07);
        }
        [data-testid="stMetric"] {
          background: #FFFFFF;
          border: 1px solid #D9E2EC;
          border-radius: 14px;
          padding: .85rem 1rem;
          box-shadow: 0 8px 24px rgba(16,42,67,.05);
        }
        [data-testid="stMetricValue"] {font-size: 1.18rem; color: #102A43;}
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] > div > div {
          border-radius: 10px;
        }
        .stButton > button, [data-testid="stFormSubmitButton"] > button {
          min-height: 3rem;
          border: 0;
          border-radius: 12px;
          font-weight: 700;
          background: linear-gradient(90deg, #0F766E 0%, #147D92 100%);
          box-shadow: 0 10px 24px rgba(15,118,110,.22);
        }
        .hero {
          position: relative;
          overflow: hidden;
          padding: 2.25rem 2.35rem;
          border-radius: 24px;
          color: white;
          background: radial-gradient(circle at 90% 10%, rgba(45,212,191,.28), transparent 32%),
                      linear-gradient(120deg, #102A43 0%, #0F4C5C 56%, #0F766E 100%);
          box-shadow: 0 20px 55px rgba(16,42,67,.20);
          margin-bottom: 1.15rem;
        }
        .hero-kicker {font-size: .77rem; font-weight: 800; letter-spacing: .14em; opacity: .78;}
        .hero h1 {font-size: 2.35rem; line-height: 1.12; margin: .55rem 0 .65rem; color: white;}
        .hero p {font-size: 1.02rem; max-width: 760px; color: #D9F2F0; margin: 0;}
        .hero-pills {display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.35rem;}
        .hero-pill {font-size: .78rem; font-weight: 650; padding: .42rem .72rem;
          border: 1px solid rgba(255,255,255,.24); border-radius: 999px;
          background: rgba(255,255,255,.10);}
        .boundary {padding: .95rem 1.1rem; border-radius: 14px;
          border: 1px solid #B8D8D5; background: #ECFDF8; color: #234E52;
          margin-bottom: 1.15rem; box-shadow: 0 8px 24px rgba(15,118,110,.05);}
        .workflow {display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin: 0 0 1.35rem;}
        .flow-card {background: rgba(255,255,255,.85); border: 1px solid #D9E2EC;
          border-radius: 14px; padding: .9rem 1rem;}
        .flow-number {display: inline-flex; width: 1.65rem; height: 1.65rem; align-items: center;
          justify-content: center; border-radius: 50%; color: white; background: #0F766E;
          font-size: .76rem; font-weight: 800; margin-right: .45rem;}
        .flow-title {font-weight: 750; color: #102A43;}
        .flow-copy {display: block; color: #627D98; font-size: .82rem; margin-top: .42rem; line-height: 1.45;}
        .section-kicker {font-size: .75rem; font-weight: 800; letter-spacing: .12em;
          color: #0F766E; margin-bottom: -.35rem;}
        .result-card {border-radius: 18px; padding: 1.25rem 1.4rem; margin: .4rem 0 1rem;
          border-left: 6px solid; box-shadow: 0 12px 30px rgba(16,42,67,.08);}
        .result-card.complete {background: #E8F8F3; border-color: #0F9D76;}
        .result-card.review {background: #FFF8E6; border-color: #E9A23B;}
        .result-card.issue {background: #FFF0F0; border-color: #D64545;}
        .result-eyebrow {font-size: .7rem; font-weight: 850; letter-spacing: .12em; color: #486581;}
        .result-title {font-size: 1.55rem; font-weight: 800; color: #102A43; margin: .18rem 0;}
        .result-detail {font-size: .9rem; color: #486581;}
        .sidebar-brand {padding: .35rem 0 1rem;}
        .sidebar-brand strong {font-size: 1.08rem;}
        .sidebar-brand span {display:block; opacity:.7; font-size:.78rem; margin-top:.2rem;}
        @media (max-width: 800px) {
          .workflow {grid-template-columns: 1fr;}
          .hero {padding: 1.6rem 1.4rem;}
          .hero h1 {font-size: 1.8rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">PE6201 · COURSEWORK PROTOTYPE</div>
          <h1>Microloan Application<br>Readiness Checker</h1>
          <p>A focused pre-check for document completeness and internal consistency,
          combining deterministic controls with bounded semantic review.</p>
          <div class="hero-pills">
            <span class="hero-pill">Deterministic rules</span>
            <span class="hero-pill">Structured Gemini output</span>
            <span class="hero-pill">Optional project-grounded RAG</span>
            <span class="hero-pill">Human authority retained</span>
          </div>
        </div>
        <div class="boundary"><strong>Scope boundary:</strong> this tool checks whether
        application materials are complete or internally consistent. It does not score
        credit, assess affordability, approve or reject a loan, or set loan terms.</div>
        <div class="workflow">
          <div class="flow-card"><span class="flow-number">1</span><span class="flow-title">Validate</span>
            <span class="flow-copy">Check the application schema and required inputs.</span></div>
          <div class="flow-card"><span class="flow-number">2</span><span class="flow-title">Inspect</span>
            <span class="flow-copy">Run exact rules and, when selected, one semantic call.</span></div>
          <div class="flow-card"><span class="flow-number">3</span><span class="flow-title">Review</span>
            <span class="flow-copy">Return a reversible status with reasons and evidence.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand"><strong>Readiness Console</strong>'
            '<span>Configure one controlled pre-check</span></div>',
            unsafe_allow_html=True,
        )
        st.subheader("Check configuration")
        mode = st.radio(
            "Method",
            ["Rule-only baseline", "Rules + Gemini", "Rules + RAG + Gemini"],
            help="Both AI options make one live structured Gemini call after submission.",
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
        elif mode == "Rules + RAG + Gemini":
            if key_ready:
                st.success("GEMINI_API_KEY is available")
            else:
                st.warning("GEMINI_API_KEY is not available in this process")
            st.info("RAG uses project-defined coursework guidance, not bank policy.")
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
        st.markdown('<div class="section-kicker">APPLICATION DETAILS</div>', unsafe_allow_html=True)
        st.subheader("Purpose and financial information")
        st.caption("Blank numeric fields are treated as missing values, not as zero.")
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

        st.markdown('<div class="section-kicker">SUPPORTING MATERIALS</div>', unsafe_allow_html=True)
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
                if mode == "Rules + RAG + Gemini":
                    result = run_rag_hybrid(
                        application,
                        client,
                        knowledge_root=PROJECT_ROOT / "knowledge_base",
                    ).to_dict()
                else:
                    result = run_hybrid(
                        application, SemanticChecker(client)
                    ).to_dict()
    except (DataValidationError, RuntimeError) as exc:
        st.error(f"The check could not run: {exc}")
        return

    st.divider()
    st.markdown('<div class="section-kicker">CHECK OUTCOME</div>', unsafe_allow_html=True)
    st.subheader("Readiness result")
    _show_outputs(st, result["outputs"])
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Application", result["application_id"])
    metric2.metric("Method", result["system"])
    metric3.metric("Requires attention", "Yes" if result["flag_worthy"] else "No")

    rule_payload = result if result["system"] == "rule_only_baseline" else result["rule_result"]
    _show_rule_issues(st, rule_payload["issues"])

    if result["system"] != "rule_only_baseline":
        security = result.get("security")
        if security and security["prompt_injection_detected"]:
            st.subheader("Input security guardrail")
            st.error(
                "The loan-purpose text contained a high-signal prompt-injection "
                "pattern. Retrieval and Gemini were skipped, and the case was "
                "routed to Manual Review."
            )
            for finding in security["findings"]:
                st.write(f"**{finding['code']}** - {finding['reason']}")

        retrieval = result.get("retrieval")
        if retrieval:
            st.subheader("Retrieved project guidance")
            st.warning(
                "This context is project-defined coursework guidance, not real bank policy."
            )
            cited = set(retrieval["cited_chunk_ids"])
            for item in retrieval["retrieved_chunks"]:
                citation_label = " · cited by model" if item["chunk_id"] in cited else ""
                with st.expander(
                    f"{item['heading']} · score {item['score']:.3f}{citation_label}"
                ):
                    st.caption(f"{item['chunk_id']} · {item['source']}")
                    st.write(item["text"])

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
