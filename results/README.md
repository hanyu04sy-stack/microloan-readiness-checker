# Evaluation Result Status

- `rule_only_final_test.json` is the completed rule-only result for all 50 frozen cases.
- `hybrid_live_checkpoint.json` contains the 50 finalized live hybrid outcomes and provides the resumable audit trail.
- `hybrid_transient_attempts.json` preserves quota-limited attempts for audit; 429 quota responses are not treated as substantive model predictions.
- `hybrid_final_test.json` is the completed full hybrid evaluation result.
- `rag_live_checkpoint.json` contains all 50 finalized RAG outcomes and the resumable audit trail.
- `rag_final_test.json` is the completed final RAG evaluation, including quality, abstention, citation, security, reliability, latency, token, and cost metrics.

The paid-tier continuation resumed from `APP_0269` without repeating the first 18 finalized cases and completed through `APP_0300`. The final result contains 44 successful semantic responses and six predefined 503 fallbacks. It achieved precision 0.857, recall 1.000, F1 0.923, and a 0.220 manual-review rate, passing the working release conditions. The earlier 429 responses remain only in the transient-attempt log.

The separately frozen RAG run completed 50 successful structured calls without retry. It achieved precision, recall, and F1 of 1.000 with a 0.100 manual-review rate. Retrieval coverage, citation coverage, and citation-identifier validity were 1.000. The subsequent independent 15-case review found 14 fully supported citations, one partially supported citation, and no unsupported citation; see `independent_review_summary.json`.
