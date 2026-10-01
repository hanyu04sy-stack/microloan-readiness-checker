"""Dependency-free lexical retrieval over the bounded project corpus.

Exports chunk models, ``chunk_markdown``, and ``ProjectKnowledgeRetriever``;
only the explicitly configured project knowledge files may enter the index.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
DEFAULT_SOURCE_FILES = (
    "project_readiness_contract.md",
    "human_review_contract.md",
)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source: str
    heading: str
    text: str

    def to_dict(self, *, score: float | None = None) -> dict:
        payload = {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "heading": self.heading,
            "text": self.text,
        }
        if score is not None:
            payload["score"] = round(score, 6)
        return payload


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: KnowledgeChunk
    score: float

    def to_dict(self) -> dict:
        return self.chunk.to_dict(score=self.score)


def _slug(value: str) -> str:
    slug = "-".join(tokenize(value))
    return slug or "section"


def chunk_markdown(path: Path) -> list[KnowledgeChunk]:
    """Split a policy Markdown file on level-two headings."""

    chunks: list[KnowledgeChunk] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        if not text:
            return
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{path.stem}#{_slug(current_heading)}",
                source=f"knowledge_base/{path.name}",
                heading=current_heading,
                text=text,
            )
        )

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_lines = []
        elif line.startswith("# "):
            continue
        else:
            current_lines.append(line)
    flush()
    return chunks


class ProjectKnowledgeRetriever:
    """Rank project-policy chunks with BM25-style lexical scoring."""

    def __init__(self, knowledge_root: Path):
        self.knowledge_root = knowledge_root
        chunks: list[KnowledgeChunk] = []
        for filename in DEFAULT_SOURCE_FILES:
            chunks.extend(chunk_markdown(knowledge_root / filename))
        if not chunks:
            raise ValueError("The project RAG knowledge base contains no chunks")
        self.chunks = tuple(chunks)
        self._tokens = [tokenize(chunk.heading + " " + chunk.text) for chunk in chunks]
        self._average_length = sum(map(len, self._tokens)) / len(self._tokens)
        self._document_frequency = Counter(
            token for tokens in self._tokens for token in set(tokens)
        )

    def retrieve(self, query: str, *, top_k: int = 3) -> tuple[RetrievedChunk, ...]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_terms = list(dict.fromkeys(tokenize(query)))
        scored: list[RetrievedChunk] = []
        total_documents = len(self.chunks)
        k1 = 1.5
        b = 0.75
        for chunk, tokens in zip(self.chunks, self._tokens):
            frequencies = Counter(tokens)
            length = len(tokens)
            score = 0.0
            for term in query_terms:
                frequency = frequencies[term]
                if not frequency:
                    continue
                document_frequency = self._document_frequency[term]
                inverse_document_frequency = math.log(
                    1 + (total_documents - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                denominator = frequency + k1 * (
                    1 - b + b * length / self._average_length
                )
                score += inverse_document_frequency * frequency * (k1 + 1) / denominator
            scored.append(RetrievedChunk(chunk=chunk, score=score))
        ranked = sorted(
            scored,
            key=lambda item: (-item.score, item.chunk.chunk_id),
        )
        positive = [item for item in ranked if item.score > 0]
        return tuple((positive or ranked)[: min(top_k, len(ranked))])

    def chunk_ids(self) -> Iterable[str]:
        return (chunk.chunk_id for chunk in self.chunks)
