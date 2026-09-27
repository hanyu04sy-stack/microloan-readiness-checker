# Synthetic Data Notes

All records in this directory are fictitious and were created for the PE6201 project evaluation. They are not sampled from a bank, fintech company, credit bureau, or real customer population.

The numeric values and category frequencies are controlled test inputs. They must not be described as representative lending statistics, realistic approval patterns, or evidence about borrower behaviour.

Application inputs and ground-truth labels are stored in separate files. The evaluated rule and hybrid systems receive application records only.

The generated files contain:

- 200 development records with draft labels;
- 50 validation records with draft labels;
- 35 scripted test records with frozen labels;
- one blank template for 15 student-authored semantic contradictions.

The generator-level `data/manifest.json` intentionally records this intermediate prerequisite. The prerequisite has now been completed: the assembled 50-case set, student-originated semantic-case provenance, independent-review status, model version, and frozen hashes are recorded separately in `data/final_test/manifest.json`.
