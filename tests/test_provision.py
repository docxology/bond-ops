"""Tests for src/bond_ops/provision.py — herdr provisioning roster."""

from __future__ import annotations

from conftest import read_log

from bond_ops import provision as pv
from bond_ops.inventory import DEFAULT_SUITE_ROOT, ROSTER


def test_build_roster_default_root():
    entries = pv.build_roster()
    assert len(entries) == 33
    assert entries[0].slug == "bond-utilities"
    assert entries[0].cwd == str(DEFAULT_SUITE_ROOT / "bond-utilities")
    assert entries[0].kind == "infra"
    # infra first (6), then films
    assert [e.kind for e in entries[:6]] == ["infra"] * 6
    assert all(e.slug == r.slug for e, r in zip(entries, ROSTER, strict=True))


def test_build_roster_prompt_resolution(tmp_path, fleet):
    prompts = tmp_path / "prompts"
    (prompts / "infra").mkdir(parents=True)
    (prompts / "infra" / "bond-ops.txt").write_text("brief", encoding="utf-8")
    (prompts / "goldfinger.txt").write_text("brief2", encoding="utf-8")
    entries = pv.build_roster(suite_root=fleet, prompt_dir=prompts)
    by = {e.slug: e for e in entries}
    assert by["bond-ops"].prompt == str(prompts / "infra" / "bond-ops.txt")
    assert by["goldfinger"].prompt == str(prompts / "goldfinger.txt")
    assert by["dr_no"].prompt is None  # no prompt file


def test_resolve_prompt_none(tmp_path):
    assert pv.resolve_prompt(tmp_path, "anything", "film") is None


def test_render_provision_script_no_prompt(fleet):
    entries = pv.build_roster(roster_=ROSTER[:2], suite_root=fleet)
    script = pv.render_provision_script(entries)
    assert (
        f'workspace create --label bond-utilities --cwd "{fleet / "bond-utilities"}" --no-focus'
        in script
    )
    assert "agent start bond-utilities --kind hermes" in script
    assert "--timeout 90000" in script
    assert "agent prompt" not in script
    assert "no mission prompt file" in script
    assert script.startswith("#!/usr/bin/env bash")


def test_render_provision_script_with_prompt(tmp_path, fleet):
    prompts = tmp_path / "prompts"
    (prompts / "infra").mkdir(parents=True)
    (prompts / "infra" / "bond-utilities.txt").write_text("BRIEF", encoding="utf-8")
    entries = pv.build_roster(roster_=ROSTER[:1], suite_root=fleet, prompt_dir=prompts)
    script = pv.render_provision_script(entries)
    assert 'agent prompt bond-utilities "$(cat' in script


def test_format_provision_readonly(fleet):
    text = pv.format_provision(roster_=ROSTER[:1], suite_root=fleet)
    assert "informational" in text.lower()
    assert "workspace create" in text


def test_execute_script_daemon_guard(fleet):
    """With no herdr on PATH, `herdr status` fails and the script aborts (safe)."""
    entries = pv.build_roster(roster_=ROSTER[:1], suite_root=fleet)
    script = pv.render_provision_script(entries)
    res = pv.execute_script(script, timeout=60)
    assert res.passed is False
    assert res.returncode == 1


def test_execute_script_success(tmp_path, fake_herdr, fleet):
    prompts = tmp_path / "prompts"
    (prompts / "infra").mkdir(parents=True)
    (prompts / "infra" / "bond-utilities.txt").write_text("BRIEF", encoding="utf-8")
    (prompts / "infra" / "bond-api.txt").write_text("B2", encoding="utf-8")
    entries = pv.build_roster(roster_=ROSTER[:2], suite_root=fleet, prompt_dir=prompts)
    script = pv.render_provision_script(entries)
    res = pv.execute_script(script, timeout=60)
    assert res.passed is True
    log = read_log(fake_herdr.log)
    assert "workspace create --label bond-utilities" in log
    assert "agent start bond-utilities --kind hermes" in log
    assert "agent prompt bond-api" in log


def test_roster_report_summary(fleet):
    entries = pv.build_roster(roster_=ROSTER[:8], suite_root=fleet)  # 6 infra + 2 films
    report = pv.roster_report(entries)
    assert report["manifest"] == "bond-ops-roster"
    assert report["summary"]["total"] == 8
    assert report["summary"]["infra"] == 6
    assert report["summary"]["film"] == 2
    assert report["summary"]["with_prompt"] == 0
    assert report["summary"]["without_prompt"] == 8
    assert len(report["entries"]) == 8
    assert report["entries"][0]["slug"] == "bond-utilities"
    assert report["entries"][0]["cwd"] == str(fleet / "bond-utilities")


def test_roster_report_with_prompts(tmp_path, fleet):
    prompts = tmp_path / "prompts"
    (prompts / "infra").mkdir(parents=True)
    (prompts / "infra" / "bond-utilities.txt").write_text("b", encoding="utf-8")
    entries = pv.build_roster(roster_=ROSTER[:1], suite_root=fleet, prompt_dir=prompts)
    report = pv.roster_report(entries)
    assert report["summary"]["with_prompt"] == 1
    assert report["summary"]["without_prompt"] == 0
    assert report["entries"][0]["prompt"] == str(prompts / "infra" / "bond-utilities.txt")
