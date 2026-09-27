# Project Readiness Contract

Source status: project-defined coursework contract, not real bank policy.

## Scope and prohibited decisions

The system checks application-material readiness before formal credit
assessment. It may identify missing documents, missing required fields, exact
numeric inconsistencies, vague purpose text, and semantic contradictions. It
must not assess affordability, default risk, creditworthiness, approval,
rejection, interest rate, pricing, or credit limit.

## Purpose category meanings

- MEDICAL_EXPENSE covers treatment, medicine, medical tests, and other
  healthcare expenses.
- EDUCATION covers tuition, course fees, required study materials, and other
  study or training expenditure.
- HOME_REPAIR covers repair or maintenance of an existing residence, not
  unrelated consumer purchases.
- SMALL_BUSINESS covers inventory, equipment, rent, and operating expenditure
  for a small business rather than personal consumption.
- VEHICLE covers purchase or repair of a vehicle used for personal or
  work-related transport.
- DEBT_CONSOLIDATION covers combining or repaying existing debts through one
  loan.
- OTHER covers a specific purpose outside the six named categories. OTHER does
  not permit vague purpose text.

## Semantic category decision rules

A category and purpose-text pair is inconsistent only when the text clearly
describes a materially different purpose category. An unusual, expensive, or
financially unwise purpose is not by itself an inconsistency. If the text could
reasonably belong to more than one category, the result should be Manual Review
rather than an invented contradiction. A blank or non-specific purpose is
missing or vague, not a category contradiction.

## Semantic issue definitions

- VAGUE_LOAN_PURPOSE means the text does not state a concrete use of funds with
  enough specificity to compare it with the form. It requires Manual Review.
- PURPOSE_CATEGORY_CONTRADICTION means the text describes a materially
  different use from the structured purpose category. It produces Inconsistent
  Information.
- PURPOSE_FORM_CONTRADICTION means the text directly contradicts another
  supplied structured fact and the contradiction depends on meaning rather
  than a fixed-value comparison. It produces Inconsistent Information.
- INSUFFICIENT_SEMANTIC_EVIDENCE means more than one reasonable interpretation
  remains. It requires Manual Review.

## Output precedence

Missing Documents applies when a required document or field is absent.
Inconsistent Information applies when a deterministic or semantic
inconsistency exists. Manual Review applies when interpretation is ambiguous,
the model reports insufficient evidence, the model call fails, or its response
fails validation. Complete applies only when no other output applies. One
application may retain more than one non-Complete output.
