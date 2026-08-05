#!/usr/bin/env python3
"""Render the canonical bond-ops manuscript figures (thin orchestrator).

Produces, under ``output/figures/``:

- ``roster_composition.png`` — from frozen roster constants;
- ``fleet_health.png`` — real health sweep over all roster packages;
- ``gate_coverage.png`` / ``gate_verdicts.png`` — a real self-gate of
  ``bond-ops`` through the venv interpreter (``--ignore=tests/test_real_fleet.py``
  so the nested gate cannot recurse into itself).

All rendering logic lives in ``bond_ops.figures``; this script only wires
inputs and prints what it wrote.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # noqa: E402

from bond_ops import figures, gates, health  # noqa: E402
from bond_ops.inventory import DEFAULT_SUITE_ROOT  # noqa: E402


def main() -> int:
    out = figures.DEFAULT_FIGURE_DIR
    figures.plot_roster_composition(out / figures.ROSTER_COMPOSITION)
    figures.plot_fleet_health(health.sweep(DEFAULT_SUITE_ROOT), out / figures.FLEET_HEALTH)
    report = gates.run_aggregate_gate(
        suite_root=DEFAULT_SUITE_ROOT,
        only_slugs=("bond-ops",),
        pytest_cmd=(
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cov=src",
            "--cov-fail-under=90",
            "--ignore=tests/test_real_fleet.py",
            "-p",
            "no:cacheprovider",
        ),
        ruff_cmd=(sys.executable, "-m", "ruff", "check", "src/"),
        mypy_cmd=(sys.executable, "-m", "mypy", "src/"),
    )
    figures.plot_gate_coverage(report, out / figures.GATE_COVERAGE)
    figures.plot_gate_verdicts(report, out / figures.GATE_VERDICTS)
    written = sorted(out.glob("*.png"))
    for path in written:
        print(f"wrote {path}")
    print(f"{len(written)} manuscript figures under {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
