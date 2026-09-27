# Step 8 - Class 6 Failure Controls

Status: complete for the current project design and available evidence. The 50-case hybrid evaluation is complete; its prototype release decision is recorded below.

## 1. Control principle and system boundary

PE6201 Class 6 asks two questions for each failure: can the failure be detected from the output, and can the action be undone? Invisible failures require monitoring or verification; irreversible actions require gates or prevention.

This project deliberately stops before credit assessment. It produces readiness labels and reasons, but it cannot approve or reject a loan, change an interest rate or credit limit, transfer money, contact a customer, or call an external action tool. Its outputs are therefore reversible, but an incorrect `Complete` label may still be invisible to the operator. The principal control problem is consequently **monitoring and verifying silent classification errors**, not authorising irreversible actions.

The chosen trade-off is explicit: the project gives up straight-through autonomy so that a Credit Operations Officer retains a review window before formal credit assessment.

## 2. Component-level failure diagnosis

| Component | Can failure be seen from its own output? | Can it be undone? | Required control |
|---|---|---|---|
| Deterministic rules | Not always. A missed semantic contradiction can look like a valid `Complete` result. | Yes; the result is advisory. | Frozen labelled evaluation, slice metrics, and comparison with the hybrid system. |
| Gemini semantic assessment | Not always. A fluent but wrong structured answer may satisfy the schema. | Yes; the result is advisory. | Structured validation, labelled evaluation, semantic-slice reporting, and human escalation when evidence is insufficient. |
| API/service call | Usually. Errors such as 503 and 429 are explicit. | Yes. | Bounded retry, checkpointing, separate attempt log, and `Manual Review` fallback. |
| Deterministic merger | Usually testable from rule and semantic inputs. | Yes. | Unit tests and a fixed precedence order that never discards rule findings. |
| External action | Not present in this version. | Not applicable. | Preserve the boundary: no approval, rejection, pricing, transfer, messaging, or tool-use authority. |

## 3. Demonstrated silent failure

The silent failure is taken from the completed rule-only run; it is not a hypothetical example.

### Case evidence

- Application: `APP_0286` in the frozen final test set.
- Structured purpose category: `EDUCATION`.
- Purpose text: the son's tuition and tutoring are already covered, and the loan will instead be used to buy a used motorcycle for delivery work.
- Frozen ground truth: `PURPOSE_CATEGORY_CONTRADICTION`, with the expected user output `Inconsistent Information`.
- Actual rule-only output: `Complete`.

The output contains no warning that the rules failed. The contradiction is only visible when the meaning of the category and purpose text is compared. This is a Class 6 silent failure.

### Detection method and observed scale

The failure was detected by joining predictions to the separately frozen labels and calculating both aggregate and sliced metrics in `results/rule_only_final_test.json`.

| Evaluation slice | False negatives | Recall |
|---|---:|---:|
| Deterministic cases | 0 | 1.000 |
| Ambiguous-purpose cases | 5 | 0.000 |
| Handwritten semantic contradictions | 15 | 0.000 |
| Full 50-case set | 20 | 0.333 |

The baseline has precision 1.000 because it raised no false alarms, but it missed 20 of 30 flag-worthy applications. This is why the instructor's precision floor of 0.70 must be reported together with the proposed recall target of 0.90. The rule-only baseline fails the recall release condition and must not be released as the readiness checker.

### Mitigation

The hybrid path sends the semantic fields to Gemini, retains every deterministic rule finding, and evaluates the result on the same frozen cases. A schema-valid model answer is not assumed to be correct; the release decision depends on precision, recall, the 15-case semantic slice, and manual-review rate. The completed hybrid run achieved precision 0.857 and recall 1.000, and detected all 15 handwritten semantic contradictions. It therefore passed the working numerical conditions on the synthetic test set.

## 4. Failure and control register

The status column distinguishes observed evidence from implemented controls and proposed production work.

| Failure mode | Evidence or risk | Control | Status and residual risk |
|---|---|---|---|
| Rule-only semantic miss | Observed: 20 false negatives, including all 15 handwritten semantic contradictions. | Hybrid semantic check; frozen labels; full-set and slice metrics; precision and recall release conditions. | Hybrid effectiveness was established on the frozen synthetic set: zero false negatives overall and all 15 handwritten cases detected. This is not production evidence. |
| Fluent but logically invalid model output | Observed before the frozen final run: a no-issue response cited evidence fields. | Exact response keys, enums, supported evidence fields, duplicate rejection, and cross-field logical invariants in `SemanticAssessment.from_mapping`. Invalid output becomes `Manual Review`. | Implemented and unit-tested. A logically valid response can still be factually wrong, so labelled evaluation remains necessary. |
| Temporary provider failure | Observed: six finalized cases exhausted retries after 503/`UNAVAILABLE`. | At most three attempts for 503/`UNAVAILABLE`; exponential waits; failure becomes `Manual Review`; checkpoint after each finalized case. | Implemented. Residual risk is extra delay and manual workload; these fallbacks contributed six of the 11 manual-review outcomes. |
| Free-tier quota exhaustion | Observed twice: the initial run paused after nine finalized cases, and the post-reset run paused at 18 when `APP_0269` reached the daily quota. | Pause the run; preserve 429 attempts separately; do not convert them into predictions or partial final metrics; resume from checkpoint later. | Implemented in the evaluation procedure. It delays completion but does not corrupt measured predictions. |
| Model availability/version change | Observed: the proposed `gemini-2.5-flash` was unavailable to the new account; the API recommended `gemini-3.8-flash`. | Explicit student approval, fixed model name, dated change note, and frozen code/data hashes in the manifest. | Implemented. Future provider changes still require a new recorded version and regression run. |
| Ground-truth leakage | Risk: the model could appear accurate if labels or document flags entered its prompt. | Labels are stored separately; only income, amount, liabilities, purpose category, and purpose text are sent to the model. | Implemented and testable. |
| Runaway calls or double retry | Risk highlighted by Class 6 denial-of-wallet guidance. | SDK retry is set to one attempt; project code owns a bounded retry loop; attempt count, retry errors, latency, and token use are logged. | Implemented. A production monthly budget ceiling is still open because no operating volume or budget has been supplied. |
| Prompt injection in purpose text | Untrusted free text could instruct the model to ignore the task. | A deterministic high-signal guardrail runs before retrieval and Gemini. A detected attack preserves rule findings, skips the model, and adds `Manual Review`. The fixed suite contains six attacks and six benign controls. | Implemented and unit-tested for the fixed suite. Paraphrased or obfuscated attacks can remain undetected, so the project does not claim prompt injection is solved. |
| Automation bias during review | A reviewer may accept a fluent reason without checking its evidence. | Show the original relevant fields, issue codes, reason, cited evidence fields, rule findings, and API status; define reviewer authority below. | Review design specified; no real workflow trial has been conducted. |
| Data or outcome drift | Purpose language and model behaviour can change after evaluation. | Frozen held-out set and version hashes support regression testing. | Partial. Production monitoring of input distribution, output balance, override/reopen rates, delayed labels, and subgroup accuracy is proposed, not implemented. |
| Privacy or sensitive-data exposure | A production lender would handle personal and financial data. | Current project uses synthetic records only and minimizes the model payload. | Adequate for this coursework dataset only. A production privacy, retention, consent, and vendor assessment is outside the evidence available here. |
| Retrieved project guidance is mistaken for bank policy | The optional RAG corpus is authored from this coursework contract, not supplied by a lender. | The corpus, prompt, interface, and audit output label every retrieved source as project-defined; only known chunk identifiers are accepted. | Implemented for the prototype. It does not establish regulatory or bank-policy grounding. |
| Invalid or fabricated RAG citation | A model could cite a source that was not retrieved. | The response schema permits only the retrieved chunk identifiers; absent, duplicated, or unknown citations invalidate the response and trigger `Manual Review`. | Implemented and unit-tested. Citation validity does not prove the cited text supports the conclusion. |

## 5. Human-review contract

Class 6 defines human-in-the-loop as a window, evidence, and authority. For this project:

### Review window

Review occurs after the readiness checker returns its result and before the application is sent for formal credit assessment. No downstream credit action is automatic.

### Evidence shown

The reviewer receives the supplied application fields relevant to the finding, deterministic issue codes and reasons, semantic issue codes and reason, cited evidence-field names, and whether the semantic call succeeded or fell back because of an error. The system must not present a bare label without this evidence.

### Reviewer authority

The Credit Operations Officer may:

- confirm that the application materials are ready;
- request correction, clarification, or missing documents;
- keep or send the case to `Manual Review`; or
- override an incorrect readiness label and record the reason.

The reviewer may not use this tool to approve or reject the loan, set pricing, or change a credit limit. The proposed override reason should become a future labelled evaluation example. The operating role is inherited from the submitted problem statement; an institution-specific procedure has not been tested.

## 6. Prompt-injection boundary

The course notes that prompt injection has no clean general fix when instructions and untrusted text share the same model context. This project therefore does not treat delimiters or a stronger prompt as a security guarantee.

The current design removes the course's “lethal trifecta” at the architecture level: it contains no real private customer dataset, gives the model no external communication channel, and gives it no action tools. A manipulated response can still misclassify readiness, but it cannot exfiltrate data or perform an external action through this system.

The final RAG candidate adds a versioned deterministic guardrail before retrieval and the model call. It detects six categories of high-signal instruction attacks and routes a detected case to `Manual Review` without sending the purpose text to Gemini. The fixed security dataset contains six attacks and six benign controls, all of which currently receive the expected decision. This bounded suite demonstrates an implemented control, not a general solution: paraphrase, encoding, multilingual attacks, or unfamiliar role-play instructions may evade pattern matching and remain residual risks.

## 7. Release and monitoring decision

The current release conditions remain:

- recall at least 0.90;
- precision at least 0.70;
- results reported for the full 50-case set and separately for the 15 handwritten semantic cases; and
- manual-review rate reported so that high recall cannot be achieved merely by escalating every case.

The completed rule-only system fails these conditions. The completed hybrid system passes them on the frozen synthetic set with recall 1.000, precision 0.857, and a 0.220 manual-review rate. This supports release only as a coursework prototype. If released beyond coursework, monitoring should add input-distribution change, output-class balance, override/reopen rate, delayed labels, and sliced accuracy, as specified in Class 6.

## 8. Defensible conclusion

The most important demonstrated failure is not an API error but a plausible `Complete` answer that is wrong. It was found only through a frozen labelled evaluation and semantic-slice reporting. The design therefore keeps exact checks in deterministic code, confines the LLM to semantic judgement, validates its structure in code, converts explicit failures to `Manual Review`, and keeps all outputs reversible before formal credit assessment. These controls reduce risk; they do not establish hybrid quality until the full evaluation is complete.
