# Final Submission Checklist

Confirmed submission facts:

- Individual End-of-Course Project.
- Weight: 44%.
- Deadline: Sunday 4 October 2026, 23:59 Singapore time.
- Deliverables: repository, recorded demonstration, and trade-off report.

The student confirmed from NTULearn on 27 September 2026 that the instructor specified no additional report word limit, report file format, or recorded-demonstration duration. Repository naming, the exact submission location, and any upload-size constraints should still be checked on the submission page itself.

## Repository

- [x] Problem and out-of-scope boundary documented.
- [x] Rule-only baseline implemented.
- [x] Rules-plus-Gemini path implemented.
- [x] Optional Streamlit demonstration interface implemented over the tested paths.
- [x] Project-defined RAG final candidate implemented with source citations.
- [x] RAG completed the preregistered 50-case evaluation and is reported separately from the earlier non-RAG run.
- [x] Frozen 50-case final set included.
- [x] Fifteen handwritten semantic cases included and separately reported.
- [x] Ground truth stored separately from inputs.
- [x] Frozen hashes recorded and verified.
- [x] Full baseline and hybrid results included.
- [x] Final RAG precision, recall, F1, abstention, citation, latency, reliability, and cost metrics recorded.
- [x] Precision, recall, F1, confusion counts, and manual-review rate reported.
- [x] Token use and cost analysis included.
- [x] Failure controls and human-review contract documented.
- [x] Thirty-three offline tests passing.
- [x] Fixed prompt-injection suite and pre-model `Manual Review` guardrail implemented.
- [x] API key excluded through `.gitignore`.
- [x] Run the clean-machine installation and reproduction check.
- [x] Initialize a local Git repository on the `main` branch.
- [x] Confirm no `.env`, API key, temporary file, or `__pycache__` is included in the submitted archive/repository.
- [x] Replace the placeholder Git author name and email, then create the first commit.
- [x] Publish the private repository: <https://github.com/hanyu04sy-stack/microloan-readiness-checker>.

## Trade-off report

- [x] English first-person Markdown report completed.
- [x] One problem, one primary user, and explicit non-use stated.
- [x] Closest publicly documented commercial tool and exact project gap researched and cited.
- [x] Known pain estimate separated from unmeasured review time, rework, labour cost, and savings.
- [x] Build-versus-buy decision explained layer by layer.
- [x] Streamlit serving, rented Gemini service, low-code decision, and qualitative time-to-deploy stated.
- [x] Rule-only baseline and target thresholds stated.
- [x] Final results and 15-case slice reported.
- [x] Abstention quality reported: 100% appropriate-review capture and 20% unnecessary-review rate among clean cases.
- [x] Leakage controls and the absence of a genuine before/after leakage experiment stated.
- [x] IMDA Model Artificial Intelligence Governance Framework, Second Edition named and mapped to controls.
- [x] Independent review scope and single-reviewer limitation stated.
- [x] External reviewer completed both independent-review stages and declaration.
- [x] Central trade-off explicitly defended.
- [x] Cost-to-serve and sensitivity included.
- [x] Risks paired with implemented controls.
- [x] Limitations stated without production claims.
- [x] Confirmed in NTULearn: no additional word-count or report-format requirement was specified.
- [x] First-person, spelling, grammar, and internal-consistency pass completed for the Markdown report.
- [ ] Student performs a final personal factual review.
- [ ] Export the approved report to a practical final format; PDF is recommended because no mandatory format was specified.

## Recorded demonstration

- [x] Modular script prepared.
- [x] Confirmed in NTULearn: no additional demonstration-duration or video-format requirement was specified.
- [ ] Record readable terminal and editor footage.
- [ ] Demonstrate the boundary, architecture, tests, silent failure, API fallback, final comparison, cost, and limitations.
- [ ] Check that no API key, `.env`, payment information, or personal notification appears in the recording.
- [ ] Watch the complete exported recording once with sound.

## Final submission

- [ ] Confirm the NTULearn submission location and naming rules.
- [ ] Submit the repository link or archive.
- [ ] Submit the recorded demonstration.
- [ ] Submit the trade-off report.
- [ ] Reopen each submitted item and verify it is accessible.
- [ ] Save submission receipts or screenshots.
