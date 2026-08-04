"""Tests for src/bond_ops/gates.py — aggregate quality gate (real subprocess)."""

from __future__ import annotations

import json
import sys

from conftest import FAKE_UV_SLOW, make_package, read_log

from bond_ops import gates as g

PYTEST = (sys.executable, "-m", "pytest", "tests/", "--cov=src", "--cov-fail-under=90")


def test_parse_coverage():
    assert g.parse_coverage("TOTAL  9 0 100%") == 100.0
    assert g.parse_coverage("TOTAL  9 4 55.56%") == 55.56
    assert g.parse_coverage("nothing here") is None
    assert g.parse_coverage("TOTAL  9 4 55.5%abc") is None  # no %-terminated token


def test_run_command_ok(tmp_path):
    res = g.run_command((sys.executable, "-c", "print('hi')"), cwd=tmp_path)
    assert res.passed is True
    assert res.output == "hi\n"
    assert res.command == (sys.executable, "-c", "print('hi')")


def test_run_command_failure(tmp_path):
    res = g.run_command((sys.executable, "-c", "raise SystemExit(3)"), cwd=tmp_path)
    assert res.passed is False
    assert res.returncode == 3


def test_gate_one_pass_real_pytest(tmp_path):
    pkg = make_package(tmp_path, "passpkg")
    res = g.gate_one(pkg, pytest_cmd=PYTEST, run_ruff=False, run_mypy=False)
    assert res.present is True
    assert res.pytest_passed is True
    assert res.passed is True
    assert res.coverage is not None and res.coverage >= 90.0


def test_gate_one_fail_real_pytest(tmp_path):
    pkg = make_package(tmp_path, "failpkg", failing=True)
    res = g.gate_one(pkg, pytest_cmd=PYTEST, run_ruff=False, run_mypy=False)
    assert res.pytest_passed is False
    assert res.passed is False


def test_gate_one_cov_low_fails(tmp_path):
    pkg = make_package(tmp_path, "lowpkg", cov_low=True)
    res = g.gate_one(pkg, pytest_cmd=PYTEST, run_ruff=False, run_mypy=False)
    assert res.pytest_passed is False
    assert res.coverage is not None and res.coverage < 90.0


def test_gate_one_not_present(tmp_path):
    res = g.gate_one(tmp_path / "missing_pkg", run_ruff=False, run_mypy=False)
    assert res.present is False
    assert res.passed is False
    assert res.error == "package directory not present"


def test_gate_one_os_error_path(tmp_path):
    pkg = make_package(tmp_path, "p")
    res = g.gate_one(
        pkg, pytest_cmd=("definitely-not-a-real-binary-zzz",), run_ruff=False, run_mypy=False
    )
    assert res.present is True
    assert res.passed is False
    assert res.error is not None


def test_gate_one_timeout(tmp_path, fake_uv):
    pkg = make_package(tmp_path, "p")
    fake_uv.put(FAKE_UV_SLOW)
    res = g.gate_one(pkg, timeout=1)
    assert res.present is True
    assert res.passed is False
    assert res.error is not None


def test_gate_one_default_uv_commands(tmp_path, fake_uv):
    pkg = make_package(tmp_path, "p")
    res = g.gate_one(pkg)  # defaults: uv run pytest + ruff + mypy
    assert res.pytest_passed is True
    assert res.ruff_passed is True
    assert res.mypy_passed is True
    assert res.passed is True
    log = read_log(fake_uv.log)
    assert "pytest tests/ --cov=src --cov-fail-under=90" in log
    assert "ruff check src/" in log
    assert "mypy src/" in log


def test_gate_one_ruff_fail_real(tmp_path):
    pkg = make_package(tmp_path, "p")
    (pkg / "src" / "p" / "dirty.py").write_text("import os\n\nx = 1\n", encoding="utf-8")
    res = g.gate_one(
        pkg,
        pytest_cmd=PYTEST,
        ruff_cmd=(sys.executable, "-m", "ruff", "check", "src/"),
        run_mypy=False,
    )
    assert res.ruff_passed is False
    assert res.passed is False


def test_gate_one_mypy_fail_real(tmp_path):
    pkg = make_package(tmp_path, "p")
    (pkg / "src" / "p" / "bad.py").write_text("x: int = 'not an int'\n", encoding="utf-8")
    res = g.gate_one(
        pkg,
        pytest_cmd=PYTEST,
        mypy_cmd=(sys.executable, "-m", "mypy", "src/"),
        run_ruff=False,
    )
    assert res.mypy_passed is False
    assert res.passed is False


def test_aggregate_gate_real_summary(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    make_package(root, "goldfinger", failing=True)
    rep = g.run_aggregate_gate(
        suite_root=root,
        only_slugs=("bond-ops", "goldfinger"),
        pytest_cmd=PYTEST,
        run_ruff=False,
        run_mypy=False,
    )
    assert rep.total == 2
    assert rep.present == 2
    assert rep.passed_count == 1
    assert rep.failed_count == 1
    assert rep.all_pass is False
    assert rep.missing_count == 0


def test_aggregate_gate_all_pass(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    rep = g.run_aggregate_gate(
        suite_root=root, only_slugs=("bond-ops",), pytest_cmd=PYTEST, run_ruff=False, run_mypy=False
    )
    assert rep.all_pass is True
    assert rep.passed_count == 1


def test_aggregate_gate_missing_and_limit(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    make_package(root, "dr_no")
    slugs = ("bond-ops", "dr_no", "goldfinger", "moonraker")  # goldfinger+moonraker missing
    rep = g.run_aggregate_gate(
        suite_root=root, only_slugs=slugs, pytest_cmd=PYTEST, run_ruff=False, run_mypy=False
    )
    assert rep.total == 4
    assert rep.present == 2
    assert rep.missing_count == 2
    lim = g.run_aggregate_gate(
        suite_root=root,
        only_slugs=slugs,
        limit=2,
        pytest_cmd=PYTEST,
        run_ruff=False,
        run_mypy=False,
    )
    assert lim.total == 2
    assert lim.passed_count == 2


def test_manifest_roundtrip_and_determinism(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "dr_no")
    rep = g.run_aggregate_gate(
        suite_root=root, only_slugs=("dr_no",), pytest_cmd=PYTEST, run_ruff=False, run_mypy=False
    )
    first = g.manifest_to_json(rep)
    second = g.manifest_to_json(rep)
    assert first == second  # deterministic (same suite state)
    data = json.loads(first)
    assert data["manifest"] == "bond-ops-gate"
    assert data["summary"]["passed"] == 1
    assert "run_timestamp" not in data  # no wall-clock in persisted artifact
    out = g.write_manifest(rep, tmp_path / "reports" / "manifest.json")
    assert out.exists()
    parsed = g.parse_manifest(out.read_text(encoding="utf-8"))
    assert parsed["manifest"] == "bond-ops-gate"
    assert "run_timestamp" not in parsed


def test_format_report_human(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "dr_no")
    rep = g.run_aggregate_gate(
        suite_root=root, only_slugs=("dr_no",), pytest_cmd=PYTEST, run_ruff=False, run_mypy=False
    )
    text = g.format_report(rep)
    assert "aggregate gate" in text
    assert "dr_no" in text
