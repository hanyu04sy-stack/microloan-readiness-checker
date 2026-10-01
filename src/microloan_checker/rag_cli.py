"""Command-line interface for the live rules-plus-RAG-plus-Gemini path.

Exports ``build_parser`` and ``main`` for one application and a bounded project
knowledge base; invalid input or provider configuration exits without a result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .gemini_client import GeminiStructuredClient
from .models import Application, DataValidationError
from .rag import run_rag_hybrid


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one rules-plus-project-RAG-plus-Gemini readiness check"
    )
    parser.add_argument("input", type=Path, help="JSON file containing one application")
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--top-k", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise DataValidationError("The RAG command accepts one JSON object")
        application = Application.from_mapping(payload)
        client = GeminiStructuredClient(model=args.model)
        result = run_rag_hybrid(
            application,
            client,
            knowledge_root=PROJECT_ROOT / "knowledge_base",
            top_k=args.top_k,
        )
    except (OSError, json.JSONDecodeError, DataValidationError, RuntimeError) as exc:
        print(f"RAG input or configuration error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
