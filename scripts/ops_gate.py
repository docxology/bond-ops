#!/usr/bin/env python3
"""Thin CLI wrapper for the bond-ops ``ops`` command (QUARTERMASTER).

Delegates entirely to :func:`bond_ops.cli.main`; this file only bootstraps
``src/`` onto ``sys.path`` so it runs without installation:

    uv run python scripts/ops_gate.py inventory --json
    uv run python scripts/ops_gate.py gate --only bond-utilities
    uv run python scripts/ops_gate.py health
    uv run python scripts/ops_gate.py roster

The installed console script ``ops`` (``[project.scripts]`` in pyproject.toml)
is the identical entry point; either spelling works.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from bond_ops.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
