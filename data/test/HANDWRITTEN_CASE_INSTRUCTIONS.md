# Handwritten Semantic Test Cases

## Why this file exists

The instructor required 15 of the 50 final test cases to be handwritten by the student and to contain contradictions that simple if or else rules cannot express. The project generator deliberately does not create those cases.

The 15 rows in `handwritten_semantic_template.csv` contain English versions of the student's Chinese scenarios, translated and revised with AI assistance at the student's request. The student subsequently accepted the revised set for the next project step. The `draft_origin` field permanently records the assistance and must not be removed.

## What the student must write

For each row:

1. Select one of the seven frozen `loan_purpose_category` values.
2. Write a specific `loan_purpose_text` whose meaning materially contradicts that category.
3. Explain the contradiction in `contradiction_rationale` without referring to a model result.
4. Personally review and rewrite each draft in your own words where necessary.
5. Change `author_check_status` from `pending_user_review` to `ready` only after checking the case against the criteria below.

Do not copy a generated development or validation case. Do not run the model on these cases while reviewing or revising them. Because the current drafts are AI-assisted, confirm with the instructor whether personally reviewing and rewriting them satisfies the requirement to "hand-write" the cases.

## Author checklist

- The text is specific rather than merely vague.
- The contradiction depends on understanding the meaning of the text.
- The contradiction is not an affordability or credit-risk judgement.
- The category and text do not contain an answer label such as contradiction, inconsistent, missing, or manual review.
- A human can explain the expected contradiction using only the category and purpose text.
- No real personal or customer information appears.
- The English text still expresses the intended scenario after your personal rewrite.

## Independent review

The current status is `not_arranged`. Do not change it unless another person or an explicitly agreed independent process actually reviews the case. The final report must not claim independent review unless it occurred.
