"""Executable versions of the documented guardrails.

Every assertion in this module exists because a document elsewhere in the
package makes a checkable claim about the code. A claim that only lives in
prose drifts silently; these tests bind each one to the tree on disk.

Covered claims:

- ``AGENTS.md`` / ``src/AGENTS.md`` / ``docs/testing_philosophy.md`` /
  ``docs/_generated/COUNTS.md``: no ``# pragma: no cover`` in ``src/bond_ops/``.
- ``docs/testing_philosophy.md``: the exact set of coverage exclusions in
  ``[tool.coverage.report]`` (a pragma substitute would otherwise slip in
  through config instead of through a comment).
- ``README.md`` / ``scripts/ops_gate.py``: the installed console script ``ops``
  is the same entry point as ``scripts/ops_gate.py``.
- ``manuscript/03_results.md``: the literal ``ops inventory`` line quoted in the
  manuscript is the line the CLI actually prints.

Real files, real installed metadata, real subprocess — no mocks.
"""

from __future__ import annotations

import re
import subprocess
import sys
from importlib.metadata import entry_points
from pathlib import Path

from conftest import PROJECT_ROOT

from bond_ops.inventory import slugs
from bond_ops.manuscript_variables import build_tokens

SRC_DIR = PROJECT_ROOT / "src" / "bond_ops"

#: The only coverage exclusions this package permits, pinned so a new one has
#: to be argued in a diff rather than typed into config.
ALLOWED_EXCLUDE_LINES = {
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
}


def _src_modules() -> list[Path]:
    mods = sorted(SRC_DIR.glob("*.py"))
    assert mods, f"no modules found under {SRC_DIR} — the sweep would be vacuous"
    return mods


def test_no_coverage_pragmas_in_src():
    """``src/bond_ops/`` contains zero ``# pragma: no cover`` comments.

    Four documents state this as a guardrail. Stating it is not enforcing it,
    so the sweep runs here: any pragma anywhere under ``src/bond_ops/`` fails
    this test with the offending file and line.
    """
    offenders: list[str] = []
    for module in _src_modules():
        for lineno, line in enumerate(module.read_text(encoding="utf-8").splitlines(), start=1):
            if "pragma: no cover" in line:
                offenders.append(f"{module.relative_to(PROJECT_ROOT)}:{lineno}: {line.strip()}")
    assert offenders == [], "coverage pragmas found in src/bond_ops/:\n" + "\n".join(offenders)


def test_coverage_exclude_lines_are_pinned():
    """``[tool.coverage.report] exclude_lines`` holds only the allowed entries.

    ``exclude_lines`` is the other way to hide a line from the gate. The
    ``if __name__ == .__main__.:`` regex is the one that currently hides real
    code (``cli.py``'s entrypoint guard); ``docs/testing_philosophy.md`` says
    so, and this test stops that list from quietly growing.
    """
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = text.split("exclude_lines = [", 1)
    assert len(block) == 2, "pyproject.toml no longer declares exclude_lines"
    body = block[1].split("]", 1)[0]
    declared = set(re.findall(r'"([^"]+)"', body))
    assert declared == ALLOWED_EXCLUDE_LINES, f"unexpected coverage exclusions: {declared}"


def test_only_the_main_guard_is_excluded_from_coverage():
    """The ``__main__`` regex hides exactly one construct: ``cli.py``'s guard.

    Keeps the documented "the only excluded line is the entrypoint guard"
    statement honest — if the pattern started matching in a second module, or
    stopped matching in ``cli.py``, this test says so.
    """
    guard = re.compile(r"^if __name__ == .__main__.:")
    matches = [
        str(m.relative_to(PROJECT_ROOT))
        for m in _src_modules()
        if any(guard.match(line) for line in m.read_text(encoding="utf-8").splitlines())
    ]
    assert matches == ["src/bond_ops/cli.py"], matches


def test_console_script_entry_point_is_declared_and_resolves():
    """``ops`` is a declared, installed console script pointing at ``cli:main``.

    The README and ``scripts/ops_gate.py`` both claim ``ops`` and
    ``python scripts/ops_gate.py`` are the same entry point. That is only true
    if ``[project.scripts]`` declares it, so read it from the *installed*
    distribution metadata rather than from the source docstring.
    """
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" in pyproject
    assert 'ops = "bond_ops.cli:main"' in pyproject

    scripts = {ep.name: ep for ep in entry_points(group="console_scripts")}
    assert "ops" in scripts, (
        "console script 'ops' is not installed — run `uv sync --all-extras`; "
        "the README claim depends on the installed entry point existing"
    )
    assert scripts["ops"].value == "bond_ops.cli:main"

    from bond_ops.cli import main as cli_main

    assert scripts["ops"].load() is cli_main


def test_installed_console_script_runs_and_matches_the_wrapper():
    """The installed ``ops`` binary and ``scripts/ops_gate.py`` agree byte-for-byte.

    "Either spelling works" is a claim about two executables, so run both.
    """
    ops_bin = Path(sys.executable).parent / "ops"
    assert ops_bin.is_file(), f"{ops_bin} not installed (run `uv sync --all-extras`)"

    via_console = subprocess.run(
        [str(ops_bin), "inventory", "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=240,
    )
    via_script = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "ops_gate.py"), "inventory", "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert via_console.returncode == 0, via_console.stderr
    assert via_script.returncode == 0, via_script.stderr
    assert via_console.stdout == via_script.stdout


def _quoted_inventory_line() -> str:
    """Pull the backticked ``ops inventory`` line out of the results section."""
    text = (PROJECT_ROOT / "manuscript" / "03_results.md").read_text(encoding="utf-8")
    match = re.search(r"A complete fleet shows `([^`]+)`", text, flags=re.S)
    assert match, "manuscript no longer quotes the `ops inventory` summary line"
    return " ".join(match.group(1).split())


def test_manuscript_quoted_inventory_line_is_what_the_cli_prints(capsys, tmp_path):
    """The manuscript's quoted CLI output must be the CLI's real output.

    Tokens are substituted from ``build_tokens()`` (the same map the manuscript
    is rendered with), then the line is required to appear verbatim in the
    output of a real ``ops inventory`` run over a fully-populated fake fleet.
    """
    from bond_ops.cli import main

    expected = _quoted_inventory_line()
    for name, value in build_tokens(PROJECT_ROOT).items():
        expected = expected.replace("{{" + name + "}}", value)
    assert "{{" not in expected, f"unsubstituted token in manuscript line: {expected}"

    root = tmp_path / "fleet"
    root.mkdir()
    for slug in slugs():
        (root / slug).mkdir()
    code = main(["inventory", "--suite-root", str(root)])
    out = capsys.readouterr().out
    assert code == 0
    assert expected in out, f"manuscript quotes {expected!r}; CLI printed:\n{out}"
