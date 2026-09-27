# Final RAG Evaluation Report

Status: automated 50-case evaluation complete; independent semantic-label and citation-support review pending.

## Evaluation contract

The final candidate combines deterministic readiness rules, project-defined retrieval, one structured Gemini semantic call, citation validation, deterministic result merging, and a pre-model prompt-injection guardrail. The same frozen 50 applications and labels were used for direct comparison with the rule-only and non-RAG hybrid systems. This supports a controlled comparison but is not a completely unseen independent dataset because the cases were already used during earlier project evaluation.

## Headline results

| System | Precision | Recall | F1 | TP | FP | TN | FN | Manual review |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Rule-only baseline | 1.000 | 0.333 | 0.500 | 10 | 0 | 20 | 20 | 0.000 |
| Rules plus Gemini, earlier run | 0.857 | 1.000 | 0.923 | 30 | 5 | 15 | 0 | 0.220 |
| Rules plus project RAG plus Gemini | 1.000 | 1.000 | 1.000 | 30 | 0 | 20 | 0 | 0.100 |

The RAG candidate passed the preregistered precision floor of 0.70 and recall floor of 0.90. All 15 handwritten semantic contradictions were detected. All five expected ambiguous cases were sent to `Manual Review`; no clean case was unnecessarily reviewed. Appropriate-review capture was 100%, and the unnecessary-review rate among clean cases was 0%.

The RAG run cannot by itself prove that retrieval caused the improvement over the earlier non-RAG run. The earlier run had six provider failures, whereas all 50 RAG calls succeeded without retry. Model and service behaviour can also vary between runs. The defensible claim is that this frozen RAG candidate achieved the reported result on this run, not that RAG guarantees perfect accuracy.

## Retrieval and citation results

| Measure | Result |
|---|---:|
| Cases sent to retrieval | 50 |
| Cases with retrieved context | 50 |
| Successful RAG responses | 50 |
| Responses with one or more citations | 50 |
| Citation identifiers returned | 109 |
| Citation identifiers valid for that case's retrieved set | 109 |
| Retrieval coverage | 100% |
| Citation coverage | 100% |
| Citation-identifier validity | 100% |

The schema requires at least one citation and allows only identifiers retrieved for that application. These figures establish coverage and identifier validity, not semantic support. Independent manual review of whether the cited passages support the model's conclusions remains pending.

## Prompt-injection guardrail

The fixed offline suite contains six high-signal prompt-injection attempts and six benign controls containing potentially confusing words. All six attacks were blocked before retrieval and the model call, and all six benign cases passed through. A detected attack preserves deterministic findings and adds `Manual Review`. The suite does not establish protection against paraphrased, obfuscated, encoded, or multilingual attacks.

## Reliability, latency, tokens, and cost

| Measure | Result |
|---|---:|
| Successful structured calls | 50/50 |
| Provider failures | 0 |
| Retries | 0 |
| Prompt tokens | 47,693 |
| Visible output tokens | 6,264 |
| Provider-reported total tokens | 83,006 |
| Estimated output plus thinking tokens | 35,313 |
| Total model latency | 194.176 seconds |
| Average model latency | 3.884 seconds per application |
| Attributable direct model cost | USD 0.1682 |
| Attributable direct model cost per incoming application | USD 0.00336 |

The cost applies the dated price configuration to returned usage metadata. No cost is invented for an attempt without usage metadata. This RAG run used more prompt tokens and cost more in direct model charges than the earlier non-RAG run; the difference in manual-review workload also reflects the different provider-failure outcomes.

## Decision and remaining boundary

The automated RAG candidate passes all preregistered numerical, citation-identifier, and fixed security-suite conditions. It remains a coursework pre-check, not a production lending system. The knowledge base is project-defined guidance rather than real bank policy, the reused 50-case set is not a new independent holdout, and independent review of handwritten labels and citation support is pending.

Evidence files:

- `data/final_test/rag_evaluation_manifest.json`
- `results/rag_final_test.json`
- `results/rag_live_checkpoint.json`
- `data/security/prompt_injection_cases.jsonl`
- `independent_review/`
