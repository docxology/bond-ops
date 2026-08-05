"""Tests for src/bond_ops/figures.py — deterministic Agg PNG generators.

Figures are rendered in-process (headless Agg) into tmp_path; assertions pin
PNG magic bytes, non-trivial size, and byte-determinism for fixed inputs.
"""

from __future__ import annotations

from pathlib import Path

from bond_ops import figures as f
from bond_ops.gates import AggregateGateReport, PackageGateResult
from bond_ops.health import HealthReport
from bond_ops.inventory import ROSTER

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _report() -> AggregateGateReport:
    results = [
        PackageGateResult("bond-ops", True, True, 96.6, True, True, True, None),
        PackageGateResult("dr_no", True, False, 55.5, False, True, False, "boom"),
        PackageGateResult("moonraker", False, None, None, None, None, False, "absent"),
    ]
    return AggregateGateReport("PROJECT BOND", "QUARTERMASTER", results)


def _assert_png(path: Path) -> None:
    data = path.read_bytes()
    assert data.startswith(PNG_MAGIC)
    assert len(data) > 500  # non-trivial size


def test_plot_roster_composition(tmp_path):
    first = f.plot_roster_composition(tmp_path / "a.png")
    second = f.plot_roster_composition(tmp_path / "b.png")
    _assert_png(first)
    assert first.read_bytes() == second.read_bytes()  # byte-deterministic


def test_plot_fleet_health(tmp_path):
    reports = [
        HealthReport(slug=r.slug, present=True, git=None, files={"x": True}) for r in ROSTER[:4]
    ]
    first = f.plot_fleet_health(reports, tmp_path / "a.png")
    second = f.plot_fleet_health(reports, tmp_path / "b.png")
    _assert_png(first)
    assert first.read_bytes() == second.read_bytes()


def test_plot_fleet_health_states(tmp_path):
    reports = [
        HealthReport(slug="good", present=True, git=None, files={"a": True}),
        HealthReport(slug="bad", present=True, git=None, files={"a": False}),
        HealthReport(slug="missing", present=False, git=None, files={}),
    ]
    path = f.plot_fleet_health(reports, tmp_path / "states.png")
    _assert_png(path)


def test_plot_fleet_health_empty(tmp_path):
    path = f.plot_fleet_health([], tmp_path / "empty.png")
    _assert_png(path)


def test_plot_gate_coverage(tmp_path):
    report = _report()
    first = f.plot_gate_coverage(report, tmp_path / "a.png")
    second = f.plot_gate_coverage(report, tmp_path / "b.png")
    _assert_png(first)
    assert first.read_bytes() == second.read_bytes()


def test_plot_gate_coverage_none_measured(tmp_path):
    report = AggregateGateReport(
        "PROJECT BOND",
        "QUARTERMASTER",
        [PackageGateResult("x", False, None, None, None, None, False, "absent")],
    )
    path = f.plot_gate_coverage(report, tmp_path / "none.png")
    _assert_png(path)


def test_plot_gate_verdicts(tmp_path):
    report = _report()
    first = f.plot_gate_verdicts(report, tmp_path / "a.png")
    second = f.plot_gate_verdicts(report, tmp_path / "b.png")
    _assert_png(first)
    assert first.read_bytes() == second.read_bytes()


def test_plot_gate_verdicts_no_present(tmp_path):
    report = AggregateGateReport(
        "PROJECT BOND",
        "QUARTERMASTER",
        [PackageGateResult("x", False, None, None, None, None, False, "absent")],
    )
    path = f.plot_gate_verdicts(report, tmp_path / "none.png")
    _assert_png(path)


def test_default_figure_dir_and_names():
    assert Path("output") / "figures" == f.DEFAULT_FIGURE_DIR
    assert f.ROSTER_COMPOSITION.endswith(".png")
    assert f.FLEET_HEALTH.endswith(".png")
    assert f.GATE_COVERAGE.endswith(".png")
    assert f.GATE_VERDICTS.endswith(".png")
