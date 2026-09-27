# Human Review Contract

Source status: project-defined coursework control, not real bank operating
policy.

## Review window

Human review occurs after the readiness result and before formal credit
assessment. No approval, rejection, pricing, messaging, transfer, or other
external action is automatic.

## Evidence shown to the reviewer

The reviewer should receive the relevant supplied application fields,
deterministic issue codes and reasons, semantic issue codes and reason, cited
evidence-field names, retrieved project-knowledge sources, and whether the
semantic call succeeded or used a fallback. A bare label is insufficient.

## Reviewer authority

The Credit Operations Officer may confirm readiness, request correction or
missing documents, keep the case in Manual Review, or override a readiness
label with a recorded reason. The officer may not use this tool to approve or
reject a loan, set pricing, or change a credit limit.

## Failure and escalation rules

A structurally invalid model response becomes Manual Review. A failed model
call becomes Manual Review without deleting deterministic findings. When
evidence is insufficient or more than one reasonable interpretation exists,
the system should abstain rather than guess. Provider failures and retrieved
context do not create credit-decision authority.
