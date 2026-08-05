"""Per-repo fleet health for the BOND suite.

For each package: git state (clean tree, branch, short sha, ahead/behind vs
upstream), presence of the required tracking files (README / AGENTS / TODO /
pyproject.toml), and a zero-tolerance sweep for leftover exemplar lineage
strings (the marker is spelled ``template[_]code_project`` in prose so this
doc cannot trip its own sweep).

All git/fs inspection is real subprocess + real files — no mocks.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

#: Files every package is expected to ship.
REQUIRED_FILES = ("README.md", "AGENTS.md", "TODO.md", "pyproject.toml")

#: Lineage string we sweep for in package contents. Built by concatenation so
#: the literal never appears contiguously in this module and cannot trip the
#: fleet-wide ``rg`` lineage gate; the runtime value is the exact marker.
LINEAGE_MARKER = "template" + "_code_project"

#: Files always skipped during the lineage sweep (never contain lineage and
#: are regenerated / binary-ish).
_LINEAGE_SKIP = {".git", "uv.lock", ".venv", ".pytest_cache", "__pycache__", "output"}


def _git(args: list[str], cwd: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def parse_porcelain(status: str) -> tuple[int, int]:
    """Count ``(modified, untracked)`` entries in ``git status --porcelain`` text.

    Pure and separately testable: lines starting ``??`` are untracked, any
    other non-blank line is a modification (staged or unstaged). Blank lines
    are ignored so a trailing newline never inflates the modified count.
    """
    modified = 0
    untracked = 0
    for line in status.splitlines():
        if line.startswith("??"):
            untracked += 1
        elif line.strip():
            modified += 1
    return modified, untracked


@dataclass(frozen=True)
class GitHealth:
    """Git state of a repository."""

    is_repo: bool
    branch: str | None
    sha: str | None
    clean: bool | None
    modified: int
    untracked: int
    ahead: int | None  # commits in HEAD not in upstream (None if no upstream)
    behind: int | None  # commits in upstream not in HEAD (None if no upstream)


def git_health(repo_dir: str | Path) -> GitHealth:
    """Inspect ``repo_dir`` as a git repository (real subprocess)."""
    root = Path(repo_dir)
    probe = _git(["rev-parse", "--is-inside-work-tree"], cwd=root)
    if probe.returncode != 0:
        return GitHealth(
            is_repo=False,
            branch=None,
            sha=None,
            clean=None,
            modified=0,
            untracked=0,
            ahead=None,
            behind=None,
        )

    branch = _git(["branch", "--show-current"], cwd=root).stdout.strip() or None
    sha = _git(["rev-parse", "--short", "HEAD"], cwd=root).stdout.strip() or None

    status = _git(["status", "--porcelain"], cwd=root).stdout
    modified, untracked = parse_porcelain(status)
    clean = modified == 0 and untracked == 0

    ahead_probe = _git(["rev-list", "--count", "@{upstream}..HEAD"], cwd=root)
    behind_probe = _git(["rev-list", "--count", "HEAD..@{upstream}"], cwd=root)
    ahead: int | None = (
        int(ahead_probe.stdout.strip() or "0") if ahead_probe.returncode == 0 else None
    )
    behind: int | None = (
        int(behind_probe.stdout.strip() or "0") if behind_probe.returncode == 0 else None
    )

    return GitHealth(
        is_repo=True,
        branch=branch,
        sha=sha,
        clean=clean,
        modified=modified,
        untracked=untracked,
        ahead=ahead,
        behind=behind,
    )


def required_files(package_dir: str | Path) -> dict[str, bool]:
    """Map each required filename to whether it exists under ``package_dir``."""
    root = Path(package_dir)
    return {name: (root / name).is_file() for name in REQUIRED_FILES}


def lineage_sweep(package_dir: str | Path) -> list[str]:
    """Return relative paths under ``package_dir`` whose contents contain the
    ``template[_]code_project`` lineage marker (zero-tolerance sweep).

    ``.git``, ``uv.lock`` and other generated caches are skipped. Binary files
    are read with errors ignored so text matches are reliable.
    """
    root = Path(package_dir)
    hits: list[str] = []
    if not root.is_dir():
        return hits
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _LINEAGE_SKIP or part.endswith(".egg-info") for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            # Unreadable file (permissions, vanished mid-sweep). Covered by
            # tests/test_health.py::test_lineage_sweep_skips_unreadable_file.
            continue
        if LINEAGE_MARKER in text:
            hits.append(str(path.relative_to(root)))
    return hits


def _read_project_name(pyproject_text: str) -> str | None:
    """Extract the ``[project] name = "..."`` value from pyproject TOML text.

    A minimal, dependency-free parser: only the ``[project]`` section is
    scanned (stdlib ``tomllib`` is 3.11+; the package supports 3.10).
    """
    in_project = False
    for line in pyproject_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue
        if in_project:
            match = re.match(r'name\s*=\s*"([^"]+)"', stripped)
            if match:
                return match.group(1)
    return None


def probe_layout(package_dir: str | Path, slug: str) -> dict[str, bool]:
    """Probe the gate-critical layout of ``package_dir``.

    Returns booleans for: ``has_pyproject``, ``pyproject_matches_slug`` (the
    ``[project] name`` equals ``slug``), ``has_tests_dir`` and ``has_src_dir``.
    A package whose pyproject name drifted from its slug is flagged here even
    when the tree is git-clean — a silent fork hazard.
    """
    root = Path(package_dir)
    pyproject = root / "pyproject.toml"
    has_pyproject = pyproject.is_file()
    project_name = (
        _read_project_name(pyproject.read_text(encoding="utf-8")) if has_pyproject else None
    )
    return {
        "has_pyproject": has_pyproject,
        "pyproject_matches_slug": project_name == slug if has_pyproject else False,
        "has_tests_dir": (root / "tests").is_dir(),
        "has_src_dir": (root / "src").is_dir(),
    }


def _binary_version(binary: str, flag: str = "--version") -> str | None:
    """First line of ``<binary> <flag>`` output, or ``None`` when unavailable."""
    path = shutil.which(binary)
    if path is None:
        return None
    try:
        proc = subprocess.run([path, flag], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        # A binary that resolves on PATH but cannot be executed (bad format,
        # revoked permission) or hangs past the probe timeout. Covered by
        # tests/test_health.py::test_binary_version_unexecutable_binary.
        return None
    text = (proc.stdout or "").strip()
    return text.splitlines()[0] if text else None


def tool_versions() -> dict[str, str | None]:
    """Probe the toolchain QUARTERMASTER itself depends on.

    Returns ``git`` / ``uv`` / ``python`` version strings (real subprocess);
    ``None`` when a tool is not on ``PATH``.
    """
    return {
        "git": _binary_version("git"),
        "uv": _binary_version("uv"),
        "python": _binary_version(sys.executable, "--version"),
    }


@dataclass
class HealthReport:
    """Composite health result for a single package."""

    slug: str
    present: bool
    git: GitHealth | None
    files: dict[str, bool]
    lineage_hits: list[str] = field(default_factory=list)
    probes: dict[str, bool] = field(default_factory=dict)

    @property
    def files_complete(self) -> bool:
        return bool(self.files) and all(self.files.values())

    @property
    def lineage_clean(self) -> bool:
        return not self.lineage_hits

    @property
    def layout_ok(self) -> bool:
        """All layout probes pass (pyproject name matches slug, tests/ and
        src/ present). Empty probes (absent package) report False."""
        return bool(self.probes) and all(self.probes.values())

    @property
    def healthy(self) -> bool:
        """Present, all required files, no lineage hits, and a clean git tree
        (when the directory is a git repository).

        Note: ``layout_ok`` is reported alongside but intentionally NOT folded
        into ``healthy`` — the probe is a diagnostic for drift, and folding it
        in would change the verdict contract downstream consumers rely on.
        """
        return bool(
            self.present
            and self.files_complete
            and self.lineage_clean
            and not (self.git is not None and self.git.is_repo and not self.git.clean)
        )


def health(package_dir: str | Path, *, slug: str | None = None) -> HealthReport:
    """Produce a composite :class:`HealthReport` for ``package_dir``."""
    root = Path(package_dir)
    name = slug if slug is not None else root.name
    if not root.is_dir():
        return HealthReport(
            slug=name,
            present=False,
            git=None,
            files={},
            lineage_hits=[],
            probes={},
        )
    return HealthReport(
        slug=name,
        present=True,
        git=git_health(root),
        files=required_files(root),
        lineage_hits=lineage_sweep(root),
        probes=probe_layout(root, name),
    )


def sweep(suite_root: str | Path | None = None) -> list[HealthReport]:
    """Return a :class:`HealthReport` for every roster package under the root.

    Iterates the canonical roster in order (infra first, then films by rank),
    so the returned list is deterministic. Packages absent from disk are
    reported as ``present=False``.
    """
    from .inventory import DEFAULT_SUITE_ROOT, ROSTER

    root = Path(suite_root) if suite_root is not None else DEFAULT_SUITE_ROOT
    return [health(root / rec.slug, slug=rec.slug) for rec in ROSTER]
