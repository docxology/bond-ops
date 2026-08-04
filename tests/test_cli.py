"""Tests for src/bond_ops/cli.py — the ``ops`` command surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import make_package

from bond_ops.cli import _parse_only, _resolve_root, main
from bond_ops.inventory import DEFAULT_SUITE_ROOT


def test_resolve_root():
    assert _resolve_root(None) == DEFAULT_SUITE_ROOT
    assert _resolve_root("/tmp/x") == Path("/tmp/x")


def test_parse_only():
    assert _parse_only("goldfinger, dr_no") == ["goldfinger", "dr_no"]
    assert _parse_only(None) == []


def test_inventory_human(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    (root / "goldfinger").mkdir()
    (root / "dr_no").mkdir()
    code = main(["inventory", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "inventory" in out
    assert "goldfinger" in out


def test_inventory_json(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    (root / "goldfinger").mkdir()
    code = main(["inventory", "--json", "--suite-root", str(root)])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["manifest"] == "bond-ops-inventory"
    assert data["summary"]["present"] == 1
    assert data["summary"]["total"] == 33


def test_gate_human_pass(capsys, tmp_path, fake_uv):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    code = main(["gate", "--only", "bond-ops", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "aggregate gate" in out


def test_gate_human_fail_exit(capsys, tmp_path, fake_uv, monkeypatch):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    monkeypatch.setenv("FAKE_UV_FAIL", "1")
    code = main(["gate", "--only", "bond-ops", "--suite-root", str(root)])
    assert code == 1


def test_gate_json(capsys, tmp_path, fake_uv):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    code = main(["gate", "--json", "--only", "bond-ops", "--suite-root", str(root)])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["manifest"] == "bond-ops-gate"
    assert data["summary"]["passed"] == 1
    assert "run_timestamp" not in data


def test_gate_limit(capsys, tmp_path, fake_uv):
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    make_package(root, "dr_no")
    code = main(
        ["gate", "--json", "--only", "bond-ops,dr_no", "--limit", "1", "--suite-root", str(root)]
    )
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["summary"]["total"] == 1


def test_gate_unknown_slug(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["gate", "--only", "nope", "--suite-root", str(root)])
    err = capsys.readouterr().err
    assert code == 2
    assert "unknown suite slug" in err


def test_health_human(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["health", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "fleet health" in out


def test_health_json(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["health", "--json", "--suite-root", str(root)])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["manifest"] == "bond-ops-health"
    assert data["summary"]["total"] == 33


def test_roster_human(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["roster", "--suite-root", str(root), "--prompt-dir", str(tmp_path / "nope")])
    out = capsys.readouterr().out
    assert code == 0
    assert "workspace create" in out


def test_roster_execute(capsys, tmp_path, fake_herdr):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["roster", "--execute", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "provision exit=0" in out


def test_unknown_subcommand():
    with pytest.raises(SystemExit) as exc:
        main(["bogus"])
    assert exc.value.code == 2
