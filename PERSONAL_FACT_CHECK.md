# Personal Final Fact Check

Use this checklist after reading `TRADE_OFF_REPORT.md` from beginning to end. This is an author confirmation, not another model or code test. Tick an item only when you personally recognise it as true from your own work, records, or supplied course material. If you are unsure, write `UNCERTAIN` beside it and revise the report to say that the fact is unknown rather than guessing.

## 1. Identity and submission

- [ ] My name, course, programme, and individual-project status are correct.
- [ ] The deadline and three deliverables match NTULearn.
- [ ] NTULearn specifies no additional word limit, report format, or demonstration duration.

## 2. Problem and scope

- [ ] I intended the primary user to be a Credit Operations Officer.
- [ ] The 40-60 applications per day figure came from my persona or problem statement, not from observed bank data.
- [ ] I agree that the tool is only a readiness pre-check and must not approve, reject, price, score, or set a loan limit.
- [ ] I did not conduct a real lender workflow study or measure time saved, rework, wages, or operational benefit.

## 3. What I built and used

- [ ] I built the deterministic rules, orchestration, evaluation, synthetic-data workflow, and Streamlit interface described in the report.
- [ ] I used the hosted Gemini model named in the report through `google-genai`.
- [ ] I did not run a low-code comparison experiment.
- [ ] I added the RAG prototype after the frozen non-RAG evaluation.
- [ ] The RAG knowledge base contains project-defined guidance, not real bank policy.
- [ ] I did not deploy the system as a production banking service.

## 4. Data provenance

- [ ] The project contains 200 development, 50 validation, and 50 frozen final-test cases.
- [ ] The final test contains 20 clean, 5 missing-document, 5 numeric or field-contradiction, 5 ambiguous-purpose, and 15 handwritten semantic-contradiction cases.
- [ ] The 15 semantic cases originated from my own Chinese scenarios and were translated or revised in English with AI assistance.
- [ ] No independent lending-domain expert reviewed those 15 cases.
- [ ] Applications and labels were frozen separately before the final model evaluation.

## 5. Results and failures

- [ ] The rule baseline results are precision 1.000, recall 0.333, and F1 0.500.
- [ ] The evaluated hybrid results are precision 0.857, recall 1.000, and F1 0.923.
- [ ] The hybrid produced 30 true positives, 5 false positives, 15 true negatives, and 0 false negatives.
- [ ] All 15 handwritten semantic contradictions were detected.
- [ ] The overall manual-review rate was 22%.
- [ ] Appropriate-review capture was 100%, and the unnecessary-review rate among clean cases was 20%.
- [ ] The final run contained 44 successful structured responses and 6 provider-failure fallbacks.
- [ ] I agree that `APP_0278` remains a false positive under the frozen label rather than changing the label after seeing the result.

## 6. Cost and evidence boundaries

- [ ] The report's USD 0.1063 direct model cost is calculated from returned usage metadata, not copied from an invoice.
- [ ] Failed calls returned no usage metadata, so the report correctly avoids inventing their cost.
- [ ] The human-review costs are course scenarios, not actual costs measured at a bank.
- [ ] The report does not claim that the system is ready for production.
- [ ] The report does not attribute the frozen 50-case metrics to RAG.

## 7. Final author decision

- [ ] I can explain the central trade-off in my own words: semantic checking removed silent misses on this synthetic set but added false positives, provider dependence, latency, cost, and human review.
- [ ] I understand and agree with every limitation stated in the report.
- [ ] I checked every external source link and did not find an unsupported claim attributed to it.
- [ ] I read the complete report aloud or slowly once and corrected anything that does not sound like my own reasoning.

Author confirmation: ____________________

Date: ____________________
