# Microloan Application Readiness Checker

This repository contains the completed experimental code and evidence for the PE6201 individual End-of-Course Project. It compares a deterministic rule-only baseline, a rules-plus-Gemini checker, and the selected rules-plus-project-RAG-plus-Gemini final candidate on the same frozen 50-case synthetic evaluation set. The RAG corpus is project-defined coursework guidance, not real bank policy.

## Demo Video

[Watch the 5-minute recorded demonstration](https://drive.google.com/drive/folders/REPLACE_WITH_YOUR_VIDEO_LINK) — face + screen recording, covers intro, architecture, live Streamlit demo, metrics, and limitations.

For a single, assessor-oriented summary of the persona, formal inputs and
outputs, architecture, target metrics, and reached metrics, see
[`PRODUCT_DOCUMENTATION.md`](PRODUCT_DOCUMENTATION.md).

## Repository Structure

```text
.
├── data/                       Synthetic evaluation data and its README
├── src/microloan_checker/      Core rule, hybrid, RAG, and CLI package
├── tests/                      Offline unit tests with simulated model clients
├── scripts/                    Data, evaluation, reporting, and demo helpers
├── results/                    Frozen machine-readable evaluation outputs
├── knowledge_base/             Bounded project-defined RAG corpus
├── independent_review/         Independent challenge-case review evidence
├── output/pdf/                 Final report PDF
├── PRODUCT_DOCUMENTATION.md    Persona, inputs, outputs, architecture, metrics
├── EVALUATION_REPORT.md        Frozen 50-case evaluation results
└── DEMO_SCRIPT.md              Recorded-demonstration script
```

## Current scope

The baseline checks:

- identity proof, income proof, and bank-statement presence;
- required application fields;
- invalid numeric values;
- exact consistency between normalized income values;
- contradictions between document-presence flags and document-derived values.

It deliberately does not:

- interpret the meaning of the free-text loan purpose;
- perform credit scoring or assess affordability;
- recommend approval, rejection, a limit, or an interest rate;
- use an agent or external credit data.

The rule-only baseline is the comparison system named in the submitted Project Problem Statement. The hybrid system adds semantic interpretation without expanding into credit decisions.

## Final result

| System | Precision | Recall | F1 | False negatives | Manual-review rate |
|---|---:|---:|---:|---:|---:|
| Rule-only baseline | 1.000 | 0.333 | 0.500 | 20 | 0.000 |
| Rules plus Gemini 3.8 Flash | 0.857 | 1.000 | 0.923 | 0 | 0.220 |
| Rules plus project RAG plus Gemini 3.8 Flash | 1.000 | 1.000 | 1.000 | 0 | 0.100 |

The final RAG run completed 50/50 structured calls without retry, returned at
least one valid retrieved-source identifier for every response, and passed the
fixed six-attack/six-benign prompt-injection suite. Automated citation validity
does not by itself prove semantic citation support. The completed independent review rated 14 of 15 challenge-case citations fully supported and one partially supported.

The hybrid system passed the predefined recall target of 0.90 and working precision floor of 0.70 on this synthetic set. All 15 handwritten semantic contradictions were detected. This is a coursework prototype result, not evidence of production readiness.

## Hybrid semantic path

The hybrid path performs exactly one structured semantic-model call per application. It:

- sends only the fields needed to compare the free-text purpose with the form;
- constrains the response with a strict JSON Schema;
- accepts only the four semantic issue codes defined in the data contract;
- rejects extra fields, unsupported evidence fields, duplicated codes, and logically inconsistent responses;
- merges semantic findings with all deterministic rule findings;
- returns `Manual Review` when the model call fails or the response is invalid;
- exposes token counts and latency when the provider returns them.

The prompt prohibits credit scoring, approval, affordability, interest-rate, limit, and default-risk judgements. No self-reported confidence score is used.

## Purpose categories

The allowed values are project-created synthetic labels, not a real bank taxonomy:

- `MEDICAL_EXPENSE`
- `EDUCATION`
- `HOME_REPAIR`
- `SMALL_BUSINESS`
- `VEHICLE`
- `DEBT_CONSOLIDATION`
- `OTHER`

## Run the tests

No third-party runtime dependency is required for the rule baseline.

```bash
python3 -m unittest discover -s tests -v
```

These tests use a simulated semantic client. They do not call Gemini and do not consume API quota.

## Run one sample

```bash
PYTHONPATH=src python3 -m microloan_checker data/sample/complete_application.json --pretty
```

The output contains the user-facing result list, issue codes, human-readable reasons, and evidence fields. Evaluation labels and split metadata are ignored by the application parser and cannot influence the rule result.

## Optional live Gemini call

The live adapter uses Google's `google-genai` package and reads `GEMINI_API_KEY`. Do not put the key in source files.

```bash
python3 -m pip install -e '.[live]'
export GEMINI_API_KEY="your-key"
PYTHONPATH=src python3 -m microloan_checker.hybrid_cli \
  data/sample/complete_application.json --model gemini-3.8-flash
```

The submitted proposal initially named Gemini 2.5 Flash. During implementation, the live API reported that `gemini-2.5-flash` was unavailable to new users and explicitly recommended `gemini-3.8-flash`. The student approved the fixed replacement model on 27 September 2026. Results must identify the model actually used.

## Run the Streamlit interface

The optional interface is a thin presentation layer over the same tested rule
and hybrid functions. Opening or editing the form does not call Gemini. A live
call occurs only after selecting `Rules + Gemini` and clicking the run button.

```bash
python3 -m pip install -e '.[app]'
set -a
source .env
set +a
streamlit run streamlit_app.py
```

For a fully offline demonstration, select `Rule-only baseline`; no API key or
Gemini quota is used. The examples load application inputs only and never read
the frozen ground-truth label file.

The third interface mode, `Rules + RAG + Gemini`, retrieves relevant sections
from the bounded `knowledge_base` corpus before making one structured Gemini
call. The page displays retrieved chunks and validated citations. This corpus is
project-defined coursework guidance, not real bank policy.

## Final RAG candidate

The RAG implementation uses dependency-free BM25-style lexical retrieval over
the project readiness and human-review contracts. It does not index course
slides, evaluation labels, result files, or customer data. Run one live case:

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m microloan_checker.rag_cli \
  data/sample/complete_application.json
```

See `RAG_PROTOTYPE.md` for the architecture, corpus boundary, citation control,
security guardrail, and evaluation status. The selected RAG candidate completed
its preregistered 50-case run; see `RAG_EVALUATION_REPORT.md` and
`results/rag_final_test.json` for the separate final evidence.

## Data status

The reproducible generator and assembly script create:

- 200 development applications;
- 50 validation applications;
- 35 scripted final-test applications;
- a 15-row semantic-case file originating from the student's Chinese scenarios and translated and revised in English with AI assistance;
- a frozen 50-case final test set under `data/final_test`.

```bash
python3 scripts/generate_synthetic_data.py
python3 scripts/validate_dataset.py
python3 scripts/assemble_final_test.py
python3 scripts/evaluate_rule_baseline.py
```

The frozen manifest preserves hashes for the applications, labels, rules, semantic prompt, and semantic-case source file. It also records that independent review has not been arranged. The generator never overwrites the semantic-case file after it exists.

## Reproduce the completed evaluations

The committed result files already contain the frozen final runs. The rule-only result can be regenerated offline:

```bash
python3 scripts/evaluate_rule_baseline.py
```

The live hybrid evaluation consumes Gemini quota and resumes from its checkpoint:

```bash
set -a
source .env
set +a
python3 scripts/evaluate_hybrid.py --delay-seconds 5
```

Do not rerun the live evaluation merely to inspect the final numbers. Use the committed offline demonstration helper instead:

```bash
python3 scripts/show_demo.py --summary
python3 scripts/show_demo.py --case APP_0286
python3 scripts/show_demo.py --case APP_0264
```

## Project evidence

- `PRODUCT_DOCUMENTATION.md`: consolidated persona, input, output, architecture, and target-versus-reached metrics.
- `EVALUATION_REPORT.md`: final baseline-versus-hybrid analysis.
- `ECONOMICS_ANALYSIS.md`: observed token use and cost-to-serve scenarios.
- `FAILURE_CONTROLS.md`: failure register, guardrails, and human-review contract.
- `TRADE_OFF_REPORT.md`: first-person trade-off report.
- `DEMO_SCRIPT.md`: modular recorded-demonstration script.
- `SUBMISSION_CHECKLIST.md`: confirmed requirements and remaining submission checks.
- `RAG_PROTOTYPE.md`: project-defined RAG final-candidate architecture and limitations.
- `RAG_EVALUATION_REPORT.md`: final RAG quality, citation, security, latency, reliability, and cost evidence.
- `independent_review/`: two-stage blind-label and citation-support review pack.
