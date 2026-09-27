# Final RAG Evaluation Contract

Status: preregistered before the final 50-case RAG run.

## System under evaluation

The final evaluated system is deterministic readiness rules plus bounded retrieval from the project-defined knowledge base plus one structured Gemini semantic call. It is not an agent and it does not use real bank policy. A deterministic prompt-injection guardrail runs before retrieval and the model call; a detected attack preserves deterministic rule findings and adds `Manual Review` without sending the purpose text to Gemini.

## Evaluation data

The system will run on the existing frozen 50-case set in `data/final_test`. Reusing the identical applications and labels enables direct comparison with the rule-only and non-RAG hybrid results and avoids inventing new labels. The limitation is that the set is no longer completely unseen during system development. The report must state this and must not describe the run as independent validation.

Before the live run, a new RAG evaluation manifest must record hashes for:

- final applications and labels;
- RAG prompt and response schema;
- retrieval code and both knowledge-base documents;
- prompt-injection guardrail and its fixed test cases;
- model adapter and model name.

No code, prompt, knowledge-base, label, or guardrail change may be made after inspecting final RAG predictions without creating a new version and a new evaluation.

## Primary quality measures

- precision, recall, F1, TP, FP, TN, and FN for flag-worthy applications;
- manual-review rate;
- appropriate-review capture;
- unnecessary-review rate among clean cases;
- results for the 15 handwritten semantic contradictions.

The existing release floors remain unchanged: recall at least 0.90 and precision at least 0.70.

## Retrieval and citation measures

- citation coverage: successful RAG responses with at least one citation divided by successful RAG responses;
- citation validity: cited chunk identifiers that were present in that case's retrieved top-k set divided by all cited identifiers;
- retrieval coverage: finalized cases with at least one retrieved chunk divided by cases sent to retrieval;
- prompt-injection pre-block rate on the fixed malicious suite;
- benign pass-through rate on the fixed benign suite.

The structured schema enforces citation presence and identifier validity. Those automated measures do not prove that a cited passage semantically supports the conclusion. Semantic citation support remains a manual audit item and must not be reported as independently verified until an external reviewer completes it.

## Reliability, latency, and cost

The run must report successful structured calls, provider failures, retries, prompt tokens, visible output tokens, total tokens, estimated output-plus-thinking tokens, total and average latency, and attributable direct model cost using the dated price configuration. Failed attempts without usage metadata must not be assigned an invented cost.

## Independent review boundary

An independent reviewer should assess the handwritten labels and, if feasible, the semantic support of RAG citations without seeing system predictions first. Reviewer role, date, cases reviewed, disagreements, and resolution must be recorded. Until that occurs, the report will state that the evaluation is author-labelled and not independently validated.
