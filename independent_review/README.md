# Independent Review Instructions

Status: completed and locked on 2026-09-28.

The reviewer must be a person other than the project author. A classmate or a person familiar with lending operations is preferable. Record the reviewer's role and any relevant experience without adding unnecessary personal information.

## Stage 1: blind semantic review

Complete `stage1_blind_semantic_review.csv` first. Do not open the frozen labels, model results, report result section, or Stage 2 file before locking Stage 1.

For each case, select one readiness output:

- `Complete`
- `Inconsistent Information`
- `Manual Review`

These 15 cases contain no intended missing-document problem. Use `Manual Review` when more than one reasonable semantic interpretation remains. Record an issue code, evidence fields, confidence, and a short explanation in the supplied columns.

After completing all 15 rows, save the file and record its SHA-256 hash or send the locked copy to the project author before beginning Stage 2.

## Stage 2: citation-support review

Only after Stage 1 is locked, open `stage2_citation_support_review.csv`. For each case, decide whether the cited project-defined text supports the model's readiness conclusion and reason:

- `SUPPORTED`: the cited text directly supports the relevant rule or interpretation;
- `PARTIAL`: some support is present, but a material step is missing or overclaimed;
- `UNSUPPORTED`: the citation does not support the conclusion or reason.

Record any unsupported or missing claim. This review judges project-document support, not compliance with real bank policy.

## Reviewer declaration

Complete `REVIEWER_DECLARATION.md`. The review is not counted as independent until all 15 rows in both stages and the declaration are complete. Run `python3 scripts/score_independent_review.py` only after the completed files are returned.
