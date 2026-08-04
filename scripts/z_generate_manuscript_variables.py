#!/usr/bin/env python3
"""Thin orchestrator: generate the manuscript ``{{TOKEN}}`` map and persist it.

Delegates to :func:`bond_ops.manuscript_variables.generate_variables`, which
reads identity tokens from ``manuscript/config.yaml`` and roster counts from
the deterministic suite constants in ``inventory.py``, then writes
``output/variables/manuscript_variables.json`` (sorted keys, deterministic).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from bond_ops import manuscript_variables as mv  # noqa: E402


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    tokens = mv.generate_variables(project_root)
    out_path = project_root / "output" / "variables" / "manuscript_variables.json"
    print(f"wrote {out_path}")
    print(json.dumps(tokens, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
