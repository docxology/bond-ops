"""Command-line interface for bond-ops (``ops``) — the QUARTERMASTER surface.

Subcommands (all read-only / informational by default):

    ops inventory [--json] [--suite-root PATH]
        Reconcile the canonical 33-slug roster against the live suite root.

    ops gate  [--json] [--only a,b] [--limit N] [--timeout S]
              [--no-ruff] [--no-mypy] [--suite-root PATH]
        Run the per-package quality gate (one subprocess per package).

    ops health  [--json] [--suite-root PATH]
        Per-repo git health, required-file presence, lineage sweep.

    ops roster  [--execute] [--suite-root PATH] [--prompt-dir PATH]
        Render (or, with --execute, run) the herdr provisioning roster.

Exit codes: ``0`` on success; ``1`` when a ``gate`` verdict fails or a hard
error occurs; ``2`` on argparse misuse (raised by argparse).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import health as health_mod
from .gates import (
    DEFAULT_MYPY_CMD,
    DEFAULT_PYTEST_CMD,
    DEFAULT_RUFF_CMD,
    DEFAULT_TIMEOUT,
    manifest_to_json,
    run_aggregate_gate,
)
from .inventory import (
    BOND_OPS_CODENAME,
    DEFAULT_SUITE_ROOT,
    SUITE_NAME,
    SUITE_SIZE,
    is_known_slug,
    reconcile,
)
from .provision import (
    build_roster,
    execute_script,
    format_provision,
    render_provision_script,
    roster_report,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _resolve_root(arg: str | None) -> Path:
    return Path(arg) if arg else DEFAULT_SUITE_ROOT


def _cmd_inventory(args: argparse.Namespace) -> int:
    root = _resolve_root(args.suite_root)
    report = reconcile(root)
    if args.json:
        _print_json(
            {
                "manifest": "bond-ops-inventory",
                "schema_version": 1,
                "suite_root": str(root),
                "summary": {
                    "total": SUITE_SIZE,
                    "present": report.present_count,
                    "missing": report.missing_count,
                    "unexpected": len(report.unexpected),
                    "complete": report.complete,
                },
                "present": list(report.present),
                "missing": list(report.missing),
                "unexpected": list(report.unexpected),
            }
        )
        return 0

    print(f"{SUITE_NAME} inventory ({BOND_OPS_CODENAME}) — {root}")
    print(
        f"present {report.present_count}/{SUITE_SIZE} · missing {report.missing_count} "
        f"· complete {report.complete}"
    )
    if report.missing:
        print("missing: " + ", ".join(report.missing))
    if report.unexpected:
        print("unexpected dirs (not in roster): " + ", ".join(report.unexpected))
    for slug in report.present:
        print(f"  present  {slug}")
    return 0


def _parse_only(value: str | None) -> list[str]:
    if not value:
        return []
    slugs = [s for s in value.replace(",", " ").split() if s]
    unknown = [s for s in slugs if not is_known_slug(s)]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown suite slug(s): {', '.join(unknown)}")
    return slugs


def _cmd_gate(args: argparse.Namespace) -> int:
    root = _resolve_root(args.suite_root)
    try:
        only = tuple(_parse_only(args.only))
    except argparse.ArgumentTypeError as exc:
        print(f"ops: error: {exc}", file=sys.stderr)
        return 2
    try:
        report = run_aggregate_gate(
            suite_root=root,
            only_slugs=only,
            limit=args.limit,
            run_ruff=not args.no_ruff,
            run_mypy=not args.no_mypy,
            timeout=args.timeout,
            pytest_cmd=tuple(args.pytest_cmd) if args.pytest_cmd else DEFAULT_PYTEST_CMD,
            ruff_cmd=tuple(args.ruff_cmd) if args.ruff_cmd else DEFAULT_RUFF_CMD,
            mypy_cmd=tuple(args.mypy_cmd) if args.mypy_cmd else DEFAULT_MYPY_CMD,
        )
    except ValueError as exc:  # negative --limit
        print(f"ops: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(manifest_to_json(report))
    else:
        from .gates import format_report

        print(format_report(report))
    return 0 if report.all_pass else 1


def _cmd_health(args: argparse.Namespace) -> int:
    root = _resolve_root(args.suite_root)
    reports = health_mod.sweep(root)
    total = len(reports)
    present = sum(1 for r in reports if r.present)
    healthy = sum(1 for r in reports if r.healthy)
    missing = total - present
    if args.json:
        _print_json(
            {
                "manifest": "bond-ops-health",
                "schema_version": 1,
                "suite_root": str(root),
                "summary": {
                    "total": total,
                    "present": present,
                    "healthy": healthy,
                    "unhealthy": present - healthy,
                    "missing": missing,
                },
                "packages": [
                    {
                        "slug": r.slug,
                        "present": r.present,
                        "is_repo": r.git.is_repo if r.git else None,
                        "clean": r.git.clean if r.git else None,
                        "branch": r.git.branch if r.git else None,
                        "ahead": r.git.ahead if r.git else None,
                        "behind": r.git.behind if r.git else None,
                        "required_files": r.files,
                        "lineage_hits": list(r.lineage_hits),
                        "probes": r.probes,
                        "layout_ok": r.layout_ok,
                        "healthy": r.healthy,
                    }
                    for r in reports
                ],
            }
        )
        return 0

    print(f"{SUITE_NAME} fleet health ({BOND_OPS_CODENAME}) — {root}")
    print(
        f"present {present}/{total} · healthy {healthy} · unhealthy {present - healthy} · missing {missing}"
    )
    for r in reports:
        if not r.present:
            print(f"  MISSING {r.slug}")
            continue
        clean = r.git.clean if r.git else None
        clean_s = "clean" if clean is True else ("dirty" if clean is False else "-")
        files = (
            "".join("R" if r.files.get("README.md") else "r")
            + "".join("A" if r.files.get("AGENTS.md") else "a")
            + "".join("T" if r.files.get("TODO.md") else "t")
            + "".join("P" if r.files.get("pyproject.toml") else "p")
        )
        lineage = len(r.lineage_hits)
        verdict = "OK" if r.healthy else "BAD"
        print(f"  {verdict:<3} {r.slug:<30} repo={clean_s:<6} files={files} lineage={lineage}")
    return 0


def _cmd_roster(args: argparse.Namespace) -> int:
    root = _resolve_root(args.suite_root)
    prompt_dir = Path(args.prompt_dir) if args.prompt_dir else (root / "_prompts")
    entries = build_roster(suite_root=root, prompt_dir=prompt_dir)
    if args.execute:
        script = render_provision_script(entries)
        result = execute_script(script)
        print(f"provision exit={result.returncode}")
        if result.output:
            print(result.output)
        return 0 if result.passed else 1
    if args.json:
        _print_json(roster_report(entries))
        return 0
    print(format_provision(suite_root=root, prompt_dir=prompt_dir))
    return 0


#: Subcommand names exposed by the ``ops`` parser, in help order. Single
#: source of truth for both :func:`main`'s dispatch table and the
#: ``CLI_COMMAND_COUNT`` manuscript token.
COMMANDS: tuple[str, ...] = ("inventory", "gate", "health", "roster")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops",
        description="BOND suite fleet operations — bond-ops QUARTERMASTER.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
        p.add_argument(
            "--suite-root", default=None, help="override the suite root (default: auto-detect)"
        )

    inv = sub.add_parser("inventory", help="reconcile the 33-package roster against disk")
    add_common(inv)

    gate = sub.add_parser("gate", help="run the per-package quality gate")
    add_common(gate)
    gate.add_argument(
        "--only", default=None, help="comma/space-separated slugs to gate (others skipped)"
    )
    gate.add_argument(
        "--limit",
        type=int,
        default=None,
        help="gate only the first N selected packages (N>=0; 0 gates nothing)",
    )
    gate.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT, help="per-command timeout (s)"
    )
    gate.add_argument("--no-ruff", action="store_true", help="skip ruff checks")
    gate.add_argument("--no-mypy", action="store_true", help="skip mypy checks")
    gate.add_argument("--pytest-cmd", default=None, nargs="+", help=argparse.SUPPRESS)
    gate.add_argument("--ruff-cmd", default=None, nargs="+", help=argparse.SUPPRESS)
    gate.add_argument("--mypy-cmd", default=None, nargs="+", help=argparse.SUPPRESS)

    hel = sub.add_parser("health", help="per-repo git health + lineage sweep")
    add_common(hel)

    roster = sub.add_parser("roster", help="render (or execute) the herdr provisioning roster")
    add_common(roster)
    roster.add_argument(
        "--execute", action="store_true", help="actually run provisioning (default: read-only)"
    )
    roster.add_argument(
        "--prompt-dir", default=None, help="directory of per-package mission prompt files"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "inventory": _cmd_inventory,
        "gate": _cmd_gate,
        "health": _cmd_health,
        "roster": _cmd_roster,
    }
    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
