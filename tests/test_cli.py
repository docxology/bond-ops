"""Tests for src/bond_ops/cli.py — the ``ops`` command surface."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pytest
from conftest import make_package, read_log

from bond_ops.cli import COMMANDS, _parse_only, _resolve_root, build_parser, main
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


def test_roster_json(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(
        ["roster", "--json", "--suite-root", str(root), "--prompt-dir", str(tmp_path / "nope")]
    )
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["manifest"] == "bond-ops-roster"
    assert data["summary"]["total"] == 33
    assert data["summary"]["infra"] == 6
    assert data["summary"]["film"] == 27
    assert data["summary"]["with_prompt"] == 0
    assert len(data["entries"]) == 33
    assert "run_timestamp" not in data


def test_health_json_has_probes(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["health", "--json", "--suite-root", str(root)])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    first = data["packages"][0]
    assert "probes" in first
    assert "layout_ok" in first
    assert first["present"] is False


def test_gate_limit_zero_gates_nothing(capsys, tmp_path, fake_uv):
    """``--limit 0`` must gate nothing, never fall back to the whole fleet."""
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    make_package(root, "dr_no")
    code = main(["gate", "--json", "--limit", "0", "--suite-root", str(root)])
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["total"] == 0
    assert data["summary"]["present"] == 0
    assert code == 1  # nothing gated -> not an all-pass verdict


def test_gate_negative_limit_is_a_usage_error(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["gate", "--limit", "-3", "--suite-root", str(root)])
    err = capsys.readouterr().err
    assert code == 2
    assert "limit must be >= 0" in err


def test_inventory_human_reports_unexpected_dirs(capsys, tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    (root / "goldfinger").mkdir()
    (root / "not_a_bond_package").mkdir()
    code = main(["inventory", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "unexpected dirs (not in roster): not_a_bond_package" in out
    assert "present  goldfinger" in out


def test_health_human_table_renders_present_package(capsys, tmp_path):
    """The human health table must actually render a present package row."""
    root = tmp_path / "fleet"
    root.mkdir()
    pkg = make_package(root, "goldfinger")
    for name in ("README.md", "AGENTS.md", "TODO.md"):
        (pkg / name).write_text("# doc\n", encoding="utf-8")
    (pkg / "pyproject.toml").write_text('[project]\nname = "goldfinger"\n', encoding="utf-8")
    code = main(["health", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "goldfinger" in out
    assert "files=RATP" in out  # every required file present
    assert "lineage=0" in out
    assert "MISSING dr_no" in out  # absent roster packages still reported


#: A real (tiny) ``herdr`` that also writes to stdout on ``agent`` steps, so the
#: CLI's "echo the provisioning transcript" branch is exercised for real.
CHATTY_HERDR = """#!/bin/sh
if [ "$1" = "status" ]; then exit 0; fi
if [ "$1" = "workspace" ]; then
  echo '{"result":{"root_pane":{"pane_id":"PANELABEL"}}}'
  exit 0
fi
echo "herdr-transcript: $*"
exit 0
"""


def test_roster_execute_prints_subprocess_output(capsys, tmp_path, monkeypatch):
    """When provisioning emits a transcript, the CLI must print it, not drop it."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "herdr").write_text(CHATTY_HERDR, encoding="utf-8")
    (bindir / "herdr").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ.get('PATH', '')}")

    root = tmp_path / "fleet"
    root.mkdir()
    code = main(["roster", "--execute", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "provision exit=0" in out
    assert "herdr-transcript: agent start bond-utilities" in out


def test_commands_constant_matches_parser_subcommands():
    """COMMANDS feeds a manuscript token — bind it to the real parser."""
    parser = build_parser()
    subparsers = [
        action
        for action in parser._subparsers._group_actions  # noqa: SLF001 - argparse introspection
        if isinstance(action, argparse._SubParsersAction)
    ]
    assert len(subparsers) == 1
    assert tuple(subparsers[0].choices) == COMMANDS


def test_inventory_human_complete_fleet(capsys, tmp_path):
    """A fully-populated root prints no missing line and reports complete."""
    from bond_ops.inventory import slugs

    root = tmp_path / "fleet"
    root.mkdir()
    for slug in slugs():
        (root / slug).mkdir()
    code = main(["inventory", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "complete True" in out
    assert "missing:" not in out


def test_health_exit_code_is_zero_even_when_packages_are_unhealthy(capsys, tmp_path):
    """``ops health`` reports; it never gates.

    The exit-code contract is ``1`` only for a failed *gate* verdict. This test
    pins the reporting-only semantics of ``health`` against a root where every
    roster package is missing (33 unhealthy, still exit 0), in both the human
    and the ``--json`` form.
    """
    root = tmp_path / "fleet"
    root.mkdir()

    code = main(["health", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert "MISSING" in out  # there really are unhealthy packages to report

    code_json = main(["health", "--json", "--suite-root", str(root)])
    data = json.loads(capsys.readouterr().out)
    assert code_json == 0
    assert data["summary"]["healthy"] == 0
    assert data["summary"]["missing"] == 33


#: A real ``uv`` that fails the gate and stamps a *different* elapsed time into
#: its output on every invocation (``$$`` is the shell's pid). Any wall-clock
#: reading that survives into the persisted manifest makes two runs differ, so
#: the determinism test below is falsifiable by construction rather than green
#: by construction.
FAKE_UV_VARYING_DURATION = """#!/bin/sh
echo "tests/test_core.py F"
echo "E       assert False"
echo "FAIL Required test coverage of 90% not reached. Total coverage: 55.56%"
echo "TOTAL                        9      4   55.56%"
echo "=========== 1 failed in $$.00s ==========="
exit 2
"""


def test_gate_json_is_byte_identical_across_two_cli_invocations(capsys, tmp_path, fake_uv):
    """Two live ``ops gate --json`` runs over an unchanged fleet print the same bytes.

    This is the manuscript's "redundant live run … asserted byte-identical
    across two invocations" claim, executed at the CLI surface. The gate runs a
    real subprocess whose output carries a *different* elapsed time each time,
    which is exactly the nondeterminism that used to leak into the persisted
    ``error`` excerpt; the two payloads must still match.
    """
    fake_uv.put(FAKE_UV_VARYING_DURATION)
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "dr_no")
    argv = ["gate", "--json", "--only", "dr_no", "--suite-root", str(root)]

    assert main(argv) == 1  # the fake gate genuinely fails
    first = capsys.readouterr().out
    assert main(argv) == 1
    second = capsys.readouterr().out

    payload = json.loads(first)
    error = payload["packages"][0]["error"]
    assert "assert False" in error  # the diagnostic text really is persisted
    assert "<elapsed>" in error  # a varying duration really was present
    assert first == second


def test_gate_pytest_cmd_accepts_dash_arguments(capsys, tmp_path, fake_uv):
    """A --pytest-cmd override must accept a full command with dash args.

    Regression for TODO C2: the old ``nargs="+"`` form stopped consuming at
    the first leading-dash token, so a real command like
    ``uv run pytest tests/ -q`` was unusable. The option is now a single
    shlex-split string; this drives it and asserts the ``-q`` token actually
    reached the subprocess (logged by the real fake-``uv`` on PATH).
    """
    root = tmp_path / "fleet"
    root.mkdir()
    make_package(root, "bond-ops")
    code = main(
        [
            "gate",
            "--json",
            "--only",
            "bond-ops",
            "--suite-root",
            str(root),
            "--pytest-cmd",
            "uv run pytest tests/ -q",
        ]
    )
    assert code == 0
    log = read_log(fake_uv.log)
    assert "-q" in log, f"the -q token did not reach the subprocess; log:\n{log}"
