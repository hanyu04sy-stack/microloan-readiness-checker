# Microloan Application Readiness Checker

This repository contains the completed experimental code and evidence for the PE6201 individual End-of-Course Project. It compares a deterministic rule-only baseline with a rules-plus-Gemini readiness checker on the same frozen 50-case synthetic evaluation set.

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

- `EVALUATION_REPORT.md`: final baseline-versus-hybrid analysis.
- `ECONOMICS_ANALYSIS.md`: observed token use and cost-to-serve scenarios.
- `FAILURE_CONTROLS.md`: failure register, guardrails, and human-review contract.
- `TRADE_OFF_REPORT_DRAFT.md`: first-person report draft.
- `DEMO_SCRIPT.md`: modular recorded-demonstration script.
- `SUBMISSION_CHECKLIST.md`: confirmed requirements and remaining submission checks.
