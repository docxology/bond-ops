"""Aggregate quality gates for the BOND fleet.

Runs the canonical per-package gate — ``uv run pytest tests/ --cov=src
--cov-fail-under=90`` — in **one package per subprocess** (never all packages
in a single pytest process, to avoid conftest collisions), plus optional ruff
and mypy checks, and emits a machine-readable JSON manifest and a human
report.

All commands are injectable so tests can drive real subprocesses against
small deterministic fake packages without invoking ``uv`` or the live fleet.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from .inventory import (
    BOND_OPS_CODENAME,
    DEFAULT_SUITE_ROOT,
    ROSTER,
    SUITE_NAME,
    PackageRecord,
)

#: Canonical per-package gate (run with cwd = the package's own directory).
DEFAULT_PYTEST_CMD = ("uv", "run", "pytest", "tests/", "--cov=src", "--cov-fail-under=90")
DEFAULT_RUFF_CMD = ("uv", "run", "ruff", "check", "src/")
DEFAULT_MYPY_CMD = ("uv", "run", "mypy", "src/")

#: How long a single subprocess gate may run before being killed (seconds).
DEFAULT_TIMEOUT = 600


@dataclass(frozen=True)
class CommandResult:
    """Outcome of one subprocess invocation."""

    command: tuple[str, ...]
    returncode: int
    passed: bool
    output: str


def run_command(
    command: tuple[str, ...] | list[str], cwd: str | Path, timeout: int = DEFAULT_TIMEOUT
) -> CommandResult:
    """Run ``command`` in ``cwd`` and capture combined output (real subprocess)."""
    proc = subprocess.run(
        list(command),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return CommandResult(
        command=tuple(command),
        returncode=proc.returncode,
        passed=proc.returncode == 0,
        output=output,
    )


def parse_coverage(output: str) -> float | None:
    """Parse the pytest-cov ``TOTAL`` line percentage from ``output``.

    Looks for a line beginning with ``TOTAL`` whose last numeric token ends in
    ``%`` (e.g. ``TOTAL  14 0 100%``). Returns ``None`` when no summary is
    present (e.g. the subprocess crashed before coverage was measured).
    """
    for line in output.splitlines():
        if line.lstrip().startswith("TOTAL"):
            for token in line.split():
                if token.endswith("%"):
                    try:
                        return float(token.rstrip("%"))
                    except ValueError:
                        return None
    return None


@dataclass
class PackageGateResult:
    """Aggregate gate outcome for one package."""

    slug: str
    present: bool
    pytest_passed: bool | None
    coverage: float | None
    ruff_passed: bool | None
    mypy_passed: bool | None
    passed: bool | None
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def gate_one(
    package_dir: str | Path,
    *,
    pytest_cmd: tuple[str, ...] = DEFAULT_PYTEST_CMD,
    ruff_cmd: tuple[str, ...] = DEFAULT_RUFF_CMD,
    mypy_cmd: tuple[str, ...] = DEFAULT_MYPY_CMD,
    run_ruff: bool = True,
    run_mypy: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> PackageGateResult:
    """Run the full gate for one package directory.

    Executes the pytest coverage gate and, optionally, ruff and mypy, each in
    its own subprocess with ``cwd=package_dir``.
    """
    pkg = Path(package_dir)
    slug = pkg.name
    if not pkg.is_dir():
        return PackageGateResult(
            slug=slug,
            present=False,
            pytest_passed=None,
            coverage=None,
            ruff_passed=None,
            mypy_passed=None,
            passed=False,
            error="package directory not present",
        )

    try:
        pytest = run_command(pytest_cmd, cwd=pkg, timeout=timeout)
        coverage = parse_coverage(pytest.output)
        ruff: CommandResult | None = None
        mypy: CommandResult | None = None
        if run_ruff:
            ruff = run_command(ruff_cmd, cwd=pkg, timeout=timeout)
        if run_mypy:
            mypy = run_command(mypy_cmd, cwd=pkg, timeout=timeout)

        ruff_ok = ruff.passed if ruff is not None else None
        mypy_ok = mypy.passed if mypy is not None else None
        # Under the canonical gate, failing ruff/mypy is informational for the
        # overall pass (coverage is the enforced floor); still record it.
        passed = pytest.passed and (ruff_ok is None or ruff_ok) and (mypy_ok is None or mypy_ok)
        return PackageGateResult(
            slug=slug,
            present=True,
            pytest_passed=pytest.passed,
            coverage=coverage,
            ruff_passed=ruff_ok,
            mypy_passed=mypy_ok,
            passed=passed,
            error=pytest.output[-800:] if not pytest.passed else None,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:  # pragma: no cover - os error path
        return PackageGateResult(
            slug=slug,
            present=True,
            pytest_passed=None,
            coverage=None,
            ruff_passed=None,
            mypy_passed=None,
            passed=False,
            error=str(exc),
        )


@dataclass
class AggregateGateReport:
    """Complete gate report across all roster packages."""

    suite_name: str
    generated_by: str
    results: list[PackageGateResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def present(self) -> int:
        return sum(1 for r in self.results if r.present)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if bool(r.passed))

    @property
    def failed_count(self) -> int:
        """Present packages whose gate verdict is a FAIL (test/lint/cov failure)."""
        return sum(1 for r in self.results if r.present and not bool(r.passed))

    @property
    def missing_count(self) -> int:
        return sum(1 for r in self.results if not r.present)

    @property
    def all_pass(self) -> bool:
        """:data:`True` when every present package passed the gate."""
        return self.present > 0 and self.failed_count == 0

    def to_dict(self) -> dict[str, object]:
        coverages = [r.coverage for r in self.results if r.present and r.coverage is not None]
        return {
            "manifest": "bond-ops-gate",
            "schema_version": 1,
            "generated_by": self.generated_by,
            "suite": self.suite_name,
            "summary": {
                "total": self.total,
                "present": self.present,
                "missing": self.missing_count,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "all_pass": self.all_pass,
                "coverage_measured": len(coverages),
                "coverage_mean": round(sum(coverages) / len(coverages), 2) if coverages else None,
                "coverage_min": min(coverages) if coverages else None,
                "coverage_max": max(coverages) if coverages else None,
            },
            "packages": [r.to_dict() for r in self.results],
        }


def run_aggregate_gate(
    roster_: tuple[PackageRecord, ...] = ROSTER,
    suite_root: str | Path | None = None,
    *,
    only_slugs: tuple[str, ...] = (),
    limit: int | None = None,
    pytest_cmd: tuple[str, ...] = DEFAULT_PYTEST_CMD,
    ruff_cmd: tuple[str, ...] = DEFAULT_RUFF_CMD,
    mypy_cmd: tuple[str, ...] = DEFAULT_MYPY_CMD,
    run_ruff: bool = True,
    run_mypy: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> AggregateGateReport:
    """Run the gate for every roster package under ``suite_root``.

    Each package is gated in its own subprocess (one package per pytest
    process). A package absent from disk is recorded as ``present=False``.

    ``only_slugs`` restricts the run to the named roster slugs (canonical order
    is preserved); ``limit`` gates at most the first ``N`` selected packages
    (useful for fast smoke runs). Both are deterministic filters only.
    """
    root = Path(suite_root) if suite_root is not None else DEFAULT_SUITE_ROOT

    selected: tuple[PackageRecord, ...] = roster_
    if only_slugs:
        wanted = set(only_slugs)
        selected = tuple(rec for rec in selected if rec.slug in wanted)
    if limit is not None and limit > 0:
        selected = selected[:limit]

    results = [
        gate_one(
            root / rec.slug,
            pytest_cmd=pytest_cmd,
            ruff_cmd=ruff_cmd,
            mypy_cmd=mypy_cmd,
            run_ruff=run_ruff,
            run_mypy=run_mypy,
            timeout=timeout,
        )
        for rec in selected
    ]
    return AggregateGateReport(
        suite_name=SUITE_NAME,
        generated_by=BOND_OPS_CODENAME,
        results=results,
    )


def build_manifest(report: AggregateGateReport) -> dict[str, object]:
    """Serialize a gate report into a machine-readable JSON-safe manifest.

    The manifest is deterministic: it embeds no wall-clock timestamp (per the
    suite guardrail against wall-clock in persisted artifacts). For a given
    suite state the manifest is byte-identical across runs.
    """
    return report.to_dict()


def manifest_to_json(report: AggregateGateReport) -> str:
    """Return the manifest as a pretty-printed JSON string."""
    return json.dumps(build_manifest(report), indent=2, sort_keys=True)


def write_manifest(report: AggregateGateReport, path: str | Path) -> Path:
    """Write the JSON manifest to ``path`` and return the resolved absolute path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(manifest_to_json(report) + "\n", encoding="utf-8")
    return target.resolve()


def parse_manifest(text: str) -> dict[str, object]:
    """Parse a manifest JSON string back into a dict (cast at the JSON boundary)."""
    return cast("dict[str, object]", json.loads(text))


def format_report(report: AggregateGateReport) -> str:
    """Render a human-readable gate report (text table)."""
    header = (
        f"{SUITE_NAME} — aggregate gate ({BOND_OPS_CODENAME})\n"
        f"packages: {report.total} total · {report.present} present · "
        f"{report.missing_count} missing · {report.passed_count} passed · "
        f"{report.failed_count} failed\n"
    )
    rows = ["slug: present  pytest  cov%  ruff  mypy  passed"]
    for r in report.results:
        rows.append(
            f"{r.slug:<28} {'yes' if r.present else 'no ':>3}  "
            f"{'PASS' if r.pytest_passed else ('FAIL' if r.pytest_passed is not None else '-- '):>4} "
            f"{'-' if r.coverage is None else f'{r.coverage:5.1f}':>6} "
            f"{'PASS' if r.ruff_passed else ('FAIL' if r.ruff_passed is not None else '-- '):>4} "
            f"{'PASS' if r.mypy_passed else ('FAIL' if r.mypy_passed is not None else '-- '):>4} "
            f"{'YES' if r.passed else 'NO '}"
        )
    return header + "\n".join(rows)
