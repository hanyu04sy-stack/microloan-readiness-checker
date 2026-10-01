"""Command-line interface for the live rules-plus-Gemini path.

Exports ``build_parser`` and ``main`` for a single application; provider and
input errors are reported without bypassing the hybrid validation contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .gemini_client import GeminiStructuredClient
from .hybrid import run_hybrid
from .models import Application, DataValidationError
from .semantic import SemanticChecker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one rules-plus-Gemini check")
    parser.add_argument("input", type=Path, help="JSON file containing one application")
    parser.add_argument("--model", default="gemini-3.8-flash")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise DataValidationError("The live hybrid command accepts one JSON object")
        application = Application.from_mapping(payload)
        client = GeminiStructuredClient(model=args.model)
        result = run_hybrid(application, SemanticChecker(client))
    except (OSError, json.JSONDecodeError, DataValidationError, RuntimeError) as exc:
        print(f"Hybrid input or configuration error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
