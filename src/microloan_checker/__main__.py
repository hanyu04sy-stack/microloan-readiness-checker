"""Package entry point for the deterministic readiness checker.

Delegates to ``cli.main`` and propagates its exit status; it intentionally
exposes only the offline rule-only path when running ``python -m``.
"""

from .cli import main

raise SystemExit(main())
