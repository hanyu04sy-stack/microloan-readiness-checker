# Project-defined RAG Final Candidate

## Status

The RAG path is implemented, selected as the final candidate, covered by
offline tests, and evaluated on the preregistered 50-case comparison. It
achieved precision, recall, and F1 of 1.000 with a 10% manual-review rate;
retrieval coverage, citation coverage, and citation-identifier validity were
all 100%. Full evidence and limitations are in `RAG_EVALUATION_REPORT.md`.

## Why this is a bounded prototype

The project has no real lender policy corpus. The RAG corpus therefore contains
only the project's confirmed readiness contract and human-review controls. It
is explicitly labelled as project-defined coursework knowledge, not bank
policy. Course slides, final-test labels, evaluation results, and customer data
are not indexed.

## Architecture

```text
application
  -> strict schema validation
  -> deterministic rule checks
  -> deterministic prompt-injection guardrail
  -> lexical retrieval from the bounded project corpus
  -> one structured Gemini call with retrieved context
  -> response and citation validation
  -> deterministic merger
  -> readiness result, evidence, retrieved chunks, and citations
```

The retriever splits the two policy documents by section and ranks chunks with
a dependency-free BM25-style lexical score. The semantic call receives the top
three chunks. Its response must cite one or more retrieved chunk identifiers;
an absent, duplicated, or unknown citation invalidates the response and routes
the case to `Manual Review`.

Before retrieval, a deterministic guardrail detects fixed high-signal attempts
to override instructions, disclose prompts, impersonate privileged roles,
force readiness outputs, or spoof source identifiers. A detected pattern skips
retrieval and Gemini, preserves deterministic findings, and routes the case to
`Manual Review`. The fixed test set contains six attacks and six benign phrases;
all currently produce the expected guardrail decision. This does not establish
protection against every paraphrase or obfuscated attack.

## Knowledge sources

- `knowledge_base/project_readiness_contract.md`
- `knowledge_base/human_review_contract.md`

These sources are derived from the project's existing data contract, issue
taxonomy, output precedence, and failure-control document. They contain no
credit-scoring or approval criteria.

## Run one live RAG check

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m microloan_checker.rag_cli \
  data/sample/complete_application.json
```

The same path is available in Streamlit as `Rules + RAG + Gemini`. A live call
occurs only after the user submits the form.

## What this prototype does not prove

- It does not prove grounding against real bank policy.
- It does not improve or replace deterministic document and numeric checks.
- Its final metrics apply only to the frozen RAG version and the reused synthetic 50-case set.
- It is not an agent: there is no planning loop, tool selection, or autonomous
  action.
- Automated citation validation does not prove semantic citation support;
  independent manual review remains pending.
