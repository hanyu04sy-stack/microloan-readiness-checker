"""Command-line entry point for the rule-only baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .models import Application, DataValidationError
from .rules import run_rule_baseline


def _evaluate_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise DataValidationError("Each application must be a JSON object")
    application = Application.from_mapping(record)
    return run_rule_baseline(application).to_dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the deterministic microloan readiness baseline."
    )
    parser.add_argument("input", type=Path, help="JSON file containing one object or a list")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            result: Any = [_evaluate_record(record) for record in payload]
        else:
            result = _evaluate_record(payload)
    except (OSError, json.JSONDecodeError, DataValidationError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
