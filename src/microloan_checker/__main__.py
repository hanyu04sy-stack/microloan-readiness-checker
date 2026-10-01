"""Command-line entry point for the deterministic readiness checker.

Input is the application JSON path and CLI options accepted by ``cli.main``.
Output is the readiness result written by that function, with its exit status
propagated to the calling shell.
"""

from .cli import main

raise SystemExit(main())
