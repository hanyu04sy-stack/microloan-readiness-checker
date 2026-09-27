# Final Evaluation Report

Status: complete for the frozen 50-case evaluation set.

## 1. Evaluation contract

Both systems were evaluated on the same frozen applications and labels, `APP_0251` through `APP_0300`. The set contains 20 clean cases, 10 deterministic problem cases, five ambiguous-purpose cases, and 15 handwritten semantic contradictions. The frozen application, label, rules, semantic prompt, model adapter, and handwritten-source hashes still match the manifest after the run.

The working release conditions, set before the final result was known, are:

- recall at least 0.90;
- precision at least 0.70; and
- reporting the 15 handwritten semantic cases separately.

Manual-review rate is also reported so that recall cannot be increased merely by sending every case to a human.

## 2. Rule-only baseline, non-RAG hybrid, and final RAG candidate

| System | Precision | Recall | F1 | TP | FP | TN | FN | Manual-review rate | Release conditions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Rule-only baseline | 1.000 | 0.333 | 0.500 | 10 | 0 | 20 | 20 | 0.000 | Fail |
| Rules plus Gemini 3.8 Flash | 0.857 | 1.000 | 0.923 | 30 | 5 | 15 | 0 | 0.220 | Pass |
| Rules plus project RAG plus Gemini 3.8 Flash | 1.000 | 1.000 | 1.000 | 30 | 0 | 20 | 0 | 0.100 | Pass |

The rule-only baseline raised no false alarms but missed 20 of the 30 flag-worthy applications. The earlier non-RAG hybrid found all 30 flag-worthy applications but produced five false positives and 11 manual-review outcomes. The final RAG candidate found all 30 flag-worthy applications, produced no false positives, and routed the five expected ambiguous cases to review.

These results support the project hypothesis on this synthetic evaluation set: semantic model assistance materially improves detection compared with deterministic rules alone. The RAG result establishes the performance of this frozen candidate on this run, but it does not prove that retrieval caused the improvement over the earlier run because provider reliability also differed. It does not establish performance on real loan applications.

## 3. Earlier non-RAG hybrid results by required slice

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

The earlier non-RAG hybrid passes the two predefined numerical release conditions on the frozen synthetic test set:

- recall `1.000 >= 0.90`;
- precision `0.857 >= 0.70`.

The later final RAG candidate also passes, with precision and recall of 1.000 and the preregistered citation-identifier and fixed security-suite conditions satisfied. This remains a **pass for the coursework prototype evaluation**, not approval for production lending use. Production use is not supported because the data are synthetic and reused, the 15 handwritten cases have no independent reviewer, the knowledge base is not bank policy, and real privacy, drift, staffing, and workflow conditions have not been tested.

## 7. Reproducible evidence

- Rule-only results: `results/rule_only_final_test.json`.
- Hybrid results: `results/hybrid_final_test.json`.
- Checkpoint audit trail: `results/hybrid_live_checkpoint.json`.
- Excluded quota attempts: `results/hybrid_transient_attempts.json`.
- Frozen set and hashes: `data/final_test/manifest.json`.

## 8. Final RAG evaluation

The project-defined RAG candidate subsequently completed a preregistered run on the same frozen 50 cases. It achieved precision, recall, and F1 of 1.000, with 30 true positives, 20 true negatives, no false positives, and no false negatives. Its manual-review rate was 10%, appropriate-review capture was 100%, and unnecessary review among clean cases was 0%.

All 50 calls returned successful structured responses without retry. Retrieval and citation coverage were 100%; all 109 cited identifiers belonged to the chunks retrieved for their cases. The run used 47,693 prompt tokens and 83,006 total tokens, took 194.176 seconds of reported model latency, and had an attributable direct model cost of USD 0.1682. These automated citation measures do not prove semantic support. The independent 15-case blind label and citation-support audit remains pending. Full evidence and interpretation are in `RAG_EVALUATION_REPORT.md`.
