# Recorded Demonstration Script

Status: content-complete draft. The supplied materials do not specify a required recording duration, so the sections are modular and can be shortened after the duration is confirmed.

## Before recording

1. Open a terminal in the repository root.
2. Increase the terminal font size so JSON is readable.
3. Do not display `.env` or the Gemini API key.
4. Keep these files ready in the editor:
   - `TRADE_OFF_REPORT.md`
   - `EVALUATION_REPORT.md`
   - `FAILURE_CONTROLS.md`
5. Run the offline test suite once before recording:

```bash
python3 -m unittest discover -s tests -q
```

6. Start the interface in a second terminal. Load the API key into the process
   only if the recording will include one intentionally triggered live call:

```bash
streamlit run streamlit_app.py
```

## Segment 1 - problem and boundary

Say:

> My project is an AI-assisted microloan application readiness checker for a Credit Operations Officer. It checks whether application materials are complete or internally inconsistent before formal credit assessment. It does not score credit, approve or reject a loan, set a price or limit, contact a customer, or use external credit data.

Show the scope-boundary panel at the top of the Streamlit interface.

## Segment 2 - architecture and trade-off

Say:

> I use deterministic Python rules for exact document and numeric checks, and one structured Gemini 3.8 Flash call for semantic interpretation of the loan-purpose text. I did not use RAG because there is no document corpus to retrieve, and I did not use an agent because the task needs one judgement rather than a tool-using loop. I own the data, orchestration, evaluation, and guardrails, while renting the foundation model.

Show:

```text
application -> schema -> rules -> one semantic call -> validation -> merger -> readiness output
```

Then open `src/microloan_checker/semantic.py` and briefly show the structured response schema and validation invariants.

## Segment 3 - reproducibility and tests

In the Streamlit interface, leave `Rule-only baseline` selected, load the sample
complete application, and click `Run readiness check`. Show the `Complete`
result, the absence of deterministic findings, and the structured audit output.

Say:

> The interface is a thin presentation layer over the same tested functions. It does not read evaluation labels, and changing the form does not call Gemini. A live semantic call occurs only when I explicitly select Rules plus Gemini and submit the form.

Then run:

```bash
python3 -m unittest discover -s tests -v
```

Say:

> These 33 offline tests do not call Gemini or consume quota. They cover data composition, leakage exclusions, deterministic rules, semantic response validation, failure fallback, result merging, interface mapping, retrieval relevance, prompt grounding, citation validation, RAG evaluation metrics, and the fixed prompt-injection guardrail suite.

For the final system, leave `Rules + RAG + Gemini` selected and show
the retrieved project-guidance sections and cited chunk identifiers. State
clearly that this is project-defined coursework knowledge, not real bank
policy, and that the frozen 50-case headline metrics belong to the non-RAG
hybrid evaluation.

## Segment 4 - demonstrated silent failure

Run:

```bash
python3 scripts/show_demo.py --case APP_0286
```

Optionally load `APP_0286` in the Streamlit interface with the rule-only mode to
show that the same rule path returns `Complete`. Use the committed demonstration
helper for the frozen hybrid result; do not rerun the live evaluation for the
recording.

Say:

> APP_0286 is the clearest silent failure. The category is education, but the purpose text says education costs are already covered and the money will first buy a motorcycle. The frozen label is Inconsistent Information. The rules output Complete because no exact field rule is broken. The hybrid system interprets the meaning and detects the contradiction. The rule output itself gives no distress signal, so the failure is only found through frozen labels and slice evaluation.

## Segment 5 - API failure and guardrail

Run:

```bash
python3 scripts/show_demo.py --case APP_0264
```

Say:

> This clean case received repeated 503 provider errors. The system did not invent a semantic answer and did not silently mark it complete. After bounded retries, deterministic code returned Manual Review. This is safe but not free: it creates a false positive and human workload.

Open `src/microloan_checker/gemini_client.py` and show the bounded retry logic. Then open `src/microloan_checker/hybrid.py` and show that an absent semantic assessment adds `Manual Review` without deleting rule findings.

## Segment 6 - final comparison

Run:

```bash
python3 scripts/show_demo.py --summary
```

Say:

> Three configurations ran on the same 50 frozen cases. The rule baseline had precision 1.000 but recall 0.333, missing 20 flag-worthy cases. The earlier non-RAG hybrid achieved precision 0.857, recall 1.000, and F1 0.923. The final RAG candidate achieved precision, recall, and F1 of 1.000, detected all 15 handwritten contradictions, and had a 10% manual-review rate. The same cases were reused, so this is a controlled comparison rather than a new independent holdout.

## Segment 7 - cost

Open `ECONOMICS_ANALYSIS.md` at the final observed usage table.

Say:

> The final RAG run reported 47,693 input tokens and an estimated 35,313 output-plus-thinking tokens. At the dated Gemini 3.8 Flash prices, attributable direct model cost was about 0.168 US dollars for 50 cases, or 0.00336 dollars per incoming application. At the observed 10% manual-review rate, the course's light and heavy fallback scenarios produce about 0.053 and 0.603 dollars per incoming application before fixed cost. These are scenarios, not measured bank costs.

## Segment 8 - conclusion and limitation

Say:

> I accept provider dependence, more prompt tokens, higher direct model cost, and a 10% review rate in exchange for eliminating the rule baseline's silent false negatives and making retrieved project sources visible. I do not accept autonomous credit action. The main limitations are synthetic reused data, pending independent review, project-defined rather than bank-policy grounding, bounded prompt-injection tests, and no production drift study. Therefore I conclude that the RAG hybrid passes the coursework prototype thresholds, not that it is ready for production lending.

End on the comparison table in `EVALUATION_REPORT.md`.
