# Evaluation Result Status

- `rule_only_final_test.json` is the completed rule-only result for all 50 frozen cases.
- `hybrid_live_checkpoint.json` contains the 50 finalized live hybrid outcomes and provides the resumable audit trail.
- `hybrid_transient_attempts.json` preserves quota-limited attempts for audit; 429 quota responses are not treated as substantive model predictions.
- `hybrid_final_test.json` is the completed full hybrid evaluation result.

The paid-tier continuation resumed from `APP_0269` without repeating the first 18 finalized cases and completed through `APP_0300`. The final result contains 44 successful semantic responses and six predefined 503 fallbacks. It achieved precision 0.857, recall 1.000, F1 0.923, and a 0.220 manual-review rate, passing the working release conditions. The earlier 429 responses remain only in the transient-attempt log.
