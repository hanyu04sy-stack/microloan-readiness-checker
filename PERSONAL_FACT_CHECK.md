# Personal Final Fact Check

Use this checklist after reading `TRADE_OFF_REPORT.md` from beginning to end. This is an author confirmation, not another model or code test. Tick an item only when you personally recognise it as true from your own work, records, or supplied course material. If you are unsure, write `UNCERTAIN` beside it and revise the report to say that the fact is unknown rather than guessing.

Evidence-backed review status on 27 September 2026: completed. Checked items below are supported by the student's explicit confirmation in the project conversation, supplied course material, repository code, frozen manifests, or saved evaluation results. Items that require the student's personal judgement or an action not yet evidenced remain unchecked.

## 1. Identity and submission

- [x] My name, course, programme, and individual-project status are correct.
- [x] The deadline and three deliverables match NTULearn.
- [x] NTULearn specifies no additional word limit, report format, or demonstration duration.

## 2. Problem and scope

- [x] I intended the primary user to be a Credit Operations Officer.
- [x] The 40-60 applications per day figure came from my persona or problem statement, not from observed bank data.
- [ ] I agree that the tool is only a readiness pre-check and must not approve, reject, price, score, or set a loan limit.
- [x] I did not conduct a real lender workflow study or measure time saved, rework, wages, or operational benefit.

## 3. What I built and used

- [ ] I built the deterministic rules, orchestration, evaluation, synthetic-data workflow, and Streamlit interface described in the report.
- [x] I used the hosted Gemini model named in the report through `google-genai`.
- [x] I did not run a low-code comparison experiment.
- [x] I added the RAG prototype after the frozen non-RAG evaluation.
- [x] The RAG knowledge base contains project-defined guidance, not real bank policy.
- [x] I did not deploy the system as a production banking service.

## 4. Data provenance

- [x] The project contains 200 development, 50 validation, and 50 frozen final-test cases.
- [x] The final test contains 20 clean, 5 missing-document, 5 numeric or field-contradiction, 5 ambiguous-purpose, and 15 handwritten semantic-contradiction cases.
- [x] The 15 semantic cases originated from my own Chinese scenarios and were translated or revised in English with AI assistance.
- [x] No independent lending-domain expert reviewed those 15 cases.
- [x] Applications and labels were frozen separately before the final model evaluation.

## 5. Results and failures

- [x] The rule baseline results are precision 1.000, recall 0.333, and F1 0.500.
- [x] The evaluated hybrid results are precision 0.857, recall 1.000, and F1 0.923.
- [x] The hybrid produced 30 true positives, 5 false positives, 15 true negatives, and 0 false negatives.
- [x] All 15 handwritten semantic contradictions were detected.
- [x] The overall manual-review rate was 22%.
- [x] Appropriate-review capture was 100%, and the unnecessary-review rate among clean cases was 20%.
- [x] The final run contained 44 successful structured responses and 6 provider-failure fallbacks.
- [ ] I agree that `APP_0278` remains a false positive under the frozen label rather than changing the label after seeing the result.

## 6. Cost and evidence boundaries

- [x] The report's USD 0.1063 direct model cost is calculated from returned usage metadata, not copied from an invoice.
- [x] Failed calls returned no usage metadata, so the report correctly avoids inventing their cost.
- [x] The human-review costs are course scenarios, not actual costs measured at a bank.
- [x] The report does not claim that the system is ready for production.
- [x] The report does not attribute the frozen 50-case metrics to RAG.

## 7. Final author decision

- [x] I can explain the central trade-off in my own words: semantic checking removed silent misses on this synthetic set but added false positives, provider dependence, latency, cost, and human review.
- [x] I understand and agree with every limitation stated in the report.
- [x] I checked every external source link and did not find an unsupported claim attributed to it.
- [x] I read the complete report aloud or slowly once and corrected anything that does not sound like my own reasoning.

Author confirmation: SUN HANYU

Date: 2026-10-02
