"""Tests for src/bond_ops/health.py — per-repo git health + lineage sweep.

Git state is exercised through real repositories created under tmp_path.
"""

from __future__ import annotations

import subprocess

from bond_ops import health as h

# Built by concatenation so this test file never contains the contiguous
# literal (which would trip the fleet-wide lineage gate); the payload is the
# exact runtime marker the sweep searches for.
MARKER = "template" + "_code_project"


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def _init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    for name in ("README.md", "AGENTS.md", "TODO.md", "pyproject.toml"):
        (root / name).write_text(f"# {name} content\n", encoding="utf-8")
    (root / ".gitignore").write_text("output/\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")


def test_git_health_clean(tmp_path):
    pkg = tmp_path / "pkg"
    _init_repo(pkg)
    gh = h.git_health(pkg)
    assert gh.is_repo is True
    assert gh.clean is True
    assert gh.modified == 0 and gh.untracked == 0
    assert gh.branch == "main"
    assert gh.sha is not None
    assert gh.ahead is None and gh.behind is None  # no upstream (local-only)


def test_git_health_dirty(tmp_path):
    pkg = tmp_path / "pkg"
    _init_repo(pkg)
    (pkg / "untracked.txt").write_text("x", encoding="utf-8")
    gh = h.git_health(pkg)
    assert gh.clean is False
    assert gh.untracked == 1
    (pkg / "README.md").write_text("changed\n", encoding="utf-8")
    gh2 = h.git_health(pkg)
    assert gh2.clean is False
    assert gh2.modified == 1


def test_git_health_not_repo(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    gh = h.git_health(pkg)
    assert gh.is_repo is False
    assert gh.clean is None
    assert gh.ahead is None and gh.behind is None
    assert gh.branch is None and gh.sha is None


def test_git_health_ahead_behind(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    work = tmp_path / "work"
    _init_repo(work)
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-q", "-u", "origin", "main")
    gh = h.git_health(work)
    assert gh.ahead == 0 and gh.behind == 0
    (work / "extra.txt").write_text("e", encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "ahead one")
    gh2 = h.git_health(work)
    assert gh2.ahead == 1 and gh2.behind == 0


def test_required_files(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "README.md").write_text("x", encoding="utf-8")
    files = h.required_files(pkg)
    assert files["README.md"] is True
    assert files["AGENTS.md"] is False
    assert len(files) == 4


def test_lineage_sweep(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "a.py").write_text(f"import os\n{MARKER} here\n", encoding="utf-8")
    (pkg / "docs").mkdir()
    (pkg / "docs" / "b.md").write_text(f"docs {MARKER}\n", encoding="utf-8")
    (pkg / "output").mkdir()
    (pkg / "output" / "gen.txt").write_text(f"{MARKER}\n", encoding="utf-8")
    hits = h.lineage_sweep(pkg)
    assert "a.py" in hits
    assert "docs/b.md" in hits
    assert not any("output" in hit for hit in hits)  # regenerable artifacts skipped


def test_lineage_sweep_clean(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "a.py").write_text("clean\n", encoding="utf-8")
    assert h.lineage_sweep(pkg) == []


def test_health_present_healthy(tmp_path):
    pkg = tmp_path / "pkg"
    _init_repo(pkg)
    report = h.health(pkg)
    assert report.present is True
    assert report.files_complete is True
    assert report.lineage_clean is True
    assert report.git is not None and report.git.is_repo is True
    assert report.healthy is True


def test_health_not_present(tmp_path):
    report = h.health(tmp_path / "nope", slug="nope")
    assert report.present is False
    assert report.healthy is False
    assert report.files_complete is False


def test_health_unhealthy_missing_file(tmp_path):
    pkg = tmp_path / "pkg"
    _init_repo(pkg)
    (pkg / "README.md").unlink()
    report = h.health(pkg)
    assert report.healthy is False
    assert report.files_complete is False


def test_sweep_over_roster(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    _init_repo(root / "bond-ops")
    _init_repo(root / "goldfinger")
    (root / "goldfinger" / "leak.txt").write_text(f"{MARKER}\n", encoding="utf-8")
    reports = h.sweep(root)
    assert len(reports) == 33  # full canonical roster
    by = {r.slug: r for r in reports}
    assert by["bond-ops"].healthy is True
    assert by["goldfinger"].healthy is False  # lineage hit
    assert by["moonraker"].present is False  # not created -> missing
