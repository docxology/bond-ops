"""Real-fleet tests — the gate runner and health probes against the live suite.

These exercise the actual QUARTERMASTER machinery against the real live
package tree under ``projects/working/bond/`` (real subprocesses, real files,
real pytest-coverage/ruff/mypy).

The gate-runner test gates **this package** (bond-ops) through the venv
interpreter with the canonical ``--cov-fail-under=90`` gate plus real ruff and
mypy; ``--ignore=tests/test_real_fleet.py`` keeps the nested run from
recursing into itself (the fake-``uv`` suite elsewhere covers the default
``uv run`` command construction). The health tests probe real sibling packages.
All tests are deterministic given the current fleet state and never skip.
"""

from __future__ import annotations

import json
import sys

from bond_ops import gates as g
from bond_ops import health as h
from bond_ops.inventory import DEFAULT_SUITE_ROOT


def test_real_fleet_gate_runner_on_self():
    pytest_cmd = (
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=src",
        f"--cov-fail-under={g.COVERAGE_FLOOR}",
        "--ignore=tests/test_real_fleet.py",
        "-p",
        "no:cacheprovider",
    )
    ruff_cmd = (sys.executable, "-m", "ruff", "check", "src/")
    mypy_cmd = (sys.executable, "-m", "mypy", "src/")

    rep = g.run_aggregate_gate(
        suite_root=DEFAULT_SUITE_ROOT,
        only_slugs=("bond-ops",),
        pytest_cmd=pytest_cmd,
        ruff_cmd=ruff_cmd,
        mypy_cmd=mypy_cmd,
    )
    assert rep.total == 1
    r = rep.results[0]
    assert r.present is True
    assert r.pytest_passed is True
    assert r.ruff_passed is True
    assert r.mypy_passed is True
    assert r.passed is True
    assert r.coverage is not None and r.coverage >= g.COVERAGE_FLOOR

    manifest = json.loads(g.manifest_to_json(rep))
    assert manifest["manifest"] == "bond-ops-gate"
    assert manifest["summary"]["passed"] == 1
    assert manifest["summary"]["failed"] == 0
    assert manifest["summary"]["coverage_measured"] == 1
    assert manifest["summary"]["coverage_mean"] == r.coverage


def test_real_fleet_health_probes():
    for slug in ("bond-ops", "bond-utilities", "goldfinger"):
        rep = h.health(DEFAULT_SUITE_ROOT / slug, slug=slug)
        assert rep.present is True
        assert rep.git is not None and rep.git.is_repo is True
        assert rep.files_complete is True
        assert rep.probes["pyproject_matches_slug"] is True
        assert rep.layout_ok is True


def test_real_fleet_toolchain():
    versions = h.tool_versions()
    assert versions["git"] is not None
    assert versions["uv"] is not None
    assert versions["python"] is not None


def test_real_fleet_film_codenames_match_roster():
    """Every present film package's declared mission codename equals the ROSTER row.

    Regression for TODO C1: bond-ops carries a codename per film slug, and a
    film package renaming itself (or this roster row drifting) used to be
    invisible. This reads each present film package's declaration as data and
    fails loudly on any divergence. Absent packages are skipped (an absent
    package is not a codename mismatch).
    """
    from bond_ops.inventory import ROSTER, declared_film_codename

    checked = 0
    for rec in (r for r in ROSTER if r.kind == "film"):
        if not (DEFAULT_SUITE_ROOT / rec.slug).is_dir():
            continue
        declared = declared_film_codename(DEFAULT_SUITE_ROOT / rec.slug, rec.slug)
        assert declared == rec.codename, (
            f"{rec.slug}: declared {declared!r} != roster {rec.codename!r} "
            "(film package renamed its mission codename, or this roster row drifted)"
        )
        checked += 1
    assert checked > 0, "no present film packages were checked"
