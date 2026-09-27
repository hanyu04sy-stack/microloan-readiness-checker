# Project-defined RAG Prototype

## Status

The optional RAG path is implemented and covered by offline tests. It has not
been run as a new frozen 50-case experiment, so the repository's existing
headline precision, recall, F1, cost, and manual-review figures continue to
describe the evaluated Rules plus Gemini system, not the RAG prototype.

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
- It does not inherit the completed 50-case performance figures.
- It is not an agent: there is no planning loop, tool selection, or autonomous
  action.
- It needs a separately frozen comparison against the non-RAG hybrid before
  any performance or cost advantage can be claimed.
