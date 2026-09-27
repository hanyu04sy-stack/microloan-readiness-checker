# Final Evaluation Report

Status: complete for the frozen 50-case evaluation set.

## 1. Evaluation contract

Both systems were evaluated on the same frozen applications and labels, `APP_0251` through `APP_0300`. The set contains 20 clean cases, 10 deterministic problem cases, five ambiguous-purpose cases, and 15 handwritten semantic contradictions. The frozen application, label, rules, semantic prompt, model adapter, and handwritten-source hashes still match the manifest after the run.

The working release conditions, set before the final result was known, are:

- recall at least 0.90;
- precision at least 0.70; and
- reporting the 15 handwritten semantic cases separately.

Manual-review rate is also reported so that recall cannot be increased merely by sending every case to a human.

## 2. Rule-only baseline versus hybrid system

| System | Precision | Recall | F1 | TP | FP | TN | FN | Manual-review rate | Release conditions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Rule-only baseline | 1.000 | 0.333 | 0.500 | 10 | 0 | 20 | 20 | 0.000 | Fail |
| Rules plus Gemini 3.8 Flash | 0.857 | 1.000 | 0.923 | 30 | 5 | 15 | 0 | 0.220 | Pass |

The rule-only baseline raised no false alarms but missed 20 of the 30 flag-worthy applications. The hybrid system found all 30 flag-worthy applications and reduced false negatives from 20 to zero, at the cost of five false positives and 11 manual-review outcomes.

This result supports the project hypothesis on this synthetic evaluation set: semantic model assistance materially improves detection compared with deterministic rules alone. It does not establish performance on real loan applications.

## 3. Hybrid results by required slice

| Slice | Cases | Precision | Recall | F1 | Manual-review rate | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| Full test | 50 | 0.857 | 1.000 | 0.923 | 0.220 | Passes both working thresholds. |
| Handwritten semantic contradictions | 15 | 1.000 | 1.000 | 1.000 | 0.000 | All 15 were detected as inconsistencies. |
| Deterministic problem cases | 10 | 1.000 | 1.000 | 1.000 | 0.200 | All remained flag-worthy; two also received `Manual Review` after 503 failures. |
| Ambiguous-purpose cases | 5 | 1.000 | 1.000 | 1.000 | 1.000 | All five were correctly routed to human review. |

The 20 clean cases produced 15 true negatives and five false positives. Four false positives were conservative `Manual Review` fallbacks after 503 failures. The fifth was a substantive model disagreement described below.

## 4. False-positive analysis

### Provider-failure fallbacks

`APP_0253`, `APP_0262`, `APP_0264`, and `APP_0267` were clean according to the frozen labels. Their semantic calls exhausted the bounded 503 retry path, so the implemented guardrail returned `Manual Review`. They count as false positives under the evaluation contract, even though conservative escalation is the intended safety behaviour.

Two additional 503 failures occurred on `APP_0252` and `APP_0266`. Those applications already contained deterministic contradictions, so the rule result kept them true positives while the semantic component also added `Manual Review`.

### Substantive model disagreement

`APP_0278` was frozen as a clean debt-consolidation case. It declared zero existing monthly liabilities while stating that existing personal debts would be combined into one repayment. Gemini classified this as `PURPOSE_FORM_CONTRADICTION`, producing the fifth false positive.

Under the frozen ground truth this remains a model error; the label was not changed after observing the prediction. The model's rationale nevertheless exposes a possible annotation ambiguity between “debt” and “monthly liabilities”. This should be independently reviewed in a future dataset version, not retroactively changed in this evaluation.

## 5. Model-call reliability and usage

| Measure | Observed value |
|---|---:|
| Finalized applications | 50 |
| Successful structured semantic responses | 44 |
| Semantic failures routed to `Manual Review` | 6 |
| Successful calls that required one or more retries | 7 retries in aggregate |
| Prompt/input tokens | 16,942 |
| Visible output tokens | 3,322 |
| Provider-reported total tokens | 41,894 |
| Estimated output plus thinking tokens | 24,952 |
| Total reported model latency | 269.306 seconds |

The six failed semantic calls remain part of the final system result because API-failure fallback was fixed before the evaluation. Quota-limited 429 attempts are retained separately in `results/hybrid_transient_attempts.json` and are not predictions.

## 6. Release decision

The hybrid system passes the two predefined numerical release conditions on the frozen synthetic test set:

- recall `1.000 >= 0.90`;
- precision `0.857 >= 0.70`.

The decision is therefore **pass for the coursework prototype evaluation**, not approval for production lending use. Production use is not supported by the evidence because the data are synthetic, the 15 handwritten cases have no independent reviewer, provider failures caused a 22% overall manual-review rate in this run, and real privacy, drift, staffing, and workflow conditions have not been tested.

## 7. Reproducible evidence

- Rule-only results: `results/rule_only_final_test.json`.
- Hybrid results: `results/hybrid_final_test.json`.
- Checkpoint audit trail: `results/hybrid_live_checkpoint.json`.
- Excluded quota attempts: `results/hybrid_transient_attempts.json`.
- Frozen set and hashes: `data/final_test/manifest.json`.
