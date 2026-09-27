"""Deterministic input guardrails for the RAG semantic path."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class SecurityFinding:
    code: str
    reason: str
    matched_text: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "reason": self.reason,
            "matched_text": self.matched_text,
        }


_INJECTION_PATTERNS: tuple[tuple[str, str, Pattern[str]], ...] = (
    (
        "INSTRUCTION_OVERRIDE_ATTEMPT",
        "The purpose text attempts to override earlier or system instructions.",
        re.compile(
            r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?"
            r"(?:previous|prior|above|earlier|system|developer)\s+"
            r"(?:instructions?|messages?|prompts?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "PROMPT_DISCLOSURE_ATTEMPT",
        "The purpose text asks for protected prompt or instruction disclosure.",
        re.compile(
            r"\b(?:reveal|show|print|display|leak|repeat)\s+"
            r"(?:the\s+|your\s+)?(?:system|developer)\s+"
            r"(?:prompt|message|instructions?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ROLE_IMPERSONATION_ATTEMPT",
        "The purpose text asks the model to assume a privileged instruction role.",
        re.compile(
            r"\b(?:act|behave|pretend)\s+as\s+(?:the\s+)?"
            r"(?:system|developer|assistant)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "OUTPUT_MANIPULATION_ATTEMPT",
        "The purpose text attempts to force a readiness output.",
        re.compile(
            r"\b(?:return|output|respond\s+with|classify(?:\s+this)?\s+as)\b"
            r".{0,60}\b(?:complete|manual\s+review|inconsistent\s+information|"
            r"missing\s+documents)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "CONTEXT_SPOOFING_ATTEMPT",
        "The purpose text contains a reserved RAG source marker.",
        re.compile(r"\bSOURCE_ID\s*:", re.IGNORECASE),
    ),
    (
        "EXPLICIT_PROMPT_ATTACK",
        "The purpose text explicitly describes a jailbreak or prompt-injection attempt.",
        re.compile(r"\b(?:jailbreak|prompt[ -]?injection)\b", re.IGNORECASE),
    ),
)


def detect_prompt_injection(text: str | None) -> tuple[SecurityFinding, ...]:
    """Return deterministic high-signal findings without interpreting loan meaning."""

    if not text:
        return ()
    findings: list[SecurityFinding] = []
    for code, reason, pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            findings.append(
                SecurityFinding(
                    code=code,
                    reason=reason,
                    matched_text=match.group(0),
                )
            )
    return tuple(findings)
