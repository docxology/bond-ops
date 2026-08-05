"""Shared test helpers — zero mocks, real subprocess + real files.

The gate / provisioning modules spawn real subprocesses; tests keep those
hermetic and deterministic by (a) running them against tmp-path fake packages
and (b) substituting small, real, executable shell scripts named ``uv`` /
``herdr`` on an override ``PATH``. No mock framework anywhere.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
from types import SimpleNamespace

import pytest

#: Headless matplotlib for deterministic figure tests (never opens a display).
os.environ.setdefault("MPLBACKEND", "Agg")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_package(
    root: pathlib.Path, slug: str, *, failing: bool = False, cov_low: bool = False
) -> pathlib.Path:
    """Create a real, minimal pytest package under ``root``.

    ``passing`` package: 100% coverage (single covered function).
    ``cov_low`` package: a second uncovered function drops line coverage < 90%.
    ``failing`` package: one test that asserts False.
    """
    modname = slug.replace("-", "_")
    pkg = root / slug
    _write(pkg / "src" / modname / "__init__.py", "")
    if cov_low:
        _write(
            pkg / "src" / modname / "core.py",
            "def g(x: int) -> int:\n    return x + 1\n\ndef h(x: int) -> int:\n    return x * 2\n",
        )
        test_body = f"from {modname}.core import g\n\ndef test_g():\n    assert g(1) == 2\n"
    else:
        _write(pkg / "src" / modname / "core.py", "def f(x: int) -> int:\n    return x + 1\n")
        test_body = f"from {modname}.core import f\n\ndef test_f():\n    assert f(1) == 2\n"
    if failing:
        test_body = "def test_fail():\n    assert False\n"
    _write(
        pkg / "tests" / "conftest.py",
        "import pathlib, sys\n"
        "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))\n",
    )
    _write(pkg / "tests" / "test_core.py", test_body)
    return pkg


#: Fake ``uv``: simulates `uv run pytest ... --cov...` output without needing a
#: real uv/project. Appends argv to ``$UV_LOG``; exits 2 + prints a FAIL line
#: when ``$FAKE_UV_FAIL`` is set (coverage below the 90% gate).
FAKE_UV = """#!/bin/sh
echo "$@" >> "$UV_LOG"
if [ "${FAKE_UV_FAIL:-0}" = "1" ]; then
  echo "FAIL Required test coverage of 90% not reached. Total coverage: 55.56%"
  echo "TOTAL                        9      4   55.56%"
  echo "1 failed in 0.01s"
  exit 2
fi
echo "tests/test_core.py ."
echo "TOTAL                        9      0   100%"
echo "3 passed in 0.01s"
exit 0
"""

#: Fake ``uv`` that hangs (for timeout / error-path coverage).
FAKE_UV_SLOW = "#!/bin/sh\nsleep 5\n"

#: Fake ``herdr``: ``status`` exits 0; ``workspace create`` emits the JSON the
#: provision script parses for ``root_pane.pane_id``; everything else exits 0.
#: Appends argv to ``$HERDR_LOG``.
FAKE_HERDR = """#!/bin/sh
echo "$@" >> "$HERDR_LOG"
cmd="$1"
if [ "$cmd" = "status" ]; then
  exit 0
fi
if [ "$cmd" = "workspace" ]; then
  echo '{"result":{"root_pane":{"pane_id":"PANELABEL"}}}'
  exit 0
fi
exit 0
"""


def _make_bin(path: pathlib.Path, script: str) -> None:
    _write(path, script)
    os.chmod(path, 0o755)


@pytest.fixture
def fake_uv(tmp_path, monkeypatch):
    """Install a fake ``uv`` on PATH; record argv to a log file."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "uv.log"
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("UV_LOG", str(log))

    def install(script: str = FAKE_UV) -> pathlib.Path:
        _make_bin(bindir / "uv", script)
        return log

    _make_bin(bindir / "uv", FAKE_UV)  # default fake uv present immediately

    return SimpleNamespace(put=install, log=log)


@pytest.fixture
def fake_herdr(tmp_path, monkeypatch):
    """Install a fake ``herdr`` on PATH; record argv to a log file."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "herdr.log"
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("HERDR_LOG", str(log))
    _make_bin(bindir / "herdr", FAKE_HERDR)
    return SimpleNamespace(log=log)


def read_log(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").strip()


@pytest.fixture
def no_herdr_path(tmp_path, monkeypatch):
    """A real ``PATH`` containing the shell and interpreter but **no** ``herdr``.

    The provisioning script resolves ``herdr`` through ``PATH``, so a test that
    means "the daemon is unreachable" has to actually make it unreachable.
    Without this, such a test inherits the developer's ambient ``PATH``; if a
    real ``herdr`` daemon happens to be running, the guard branch is never
    taken and the script executes real ``workspace create`` / ``agent start``
    calls against the live daemon.

    Only ``PATH`` is redirected, and the two binaries the script genuinely
    needs are real symlinks to the real tools — this is environment isolation,
    not object substitution.
    """
    bindir = tmp_path / "sterile-bin"
    bindir.mkdir()
    for tool in ("bash", "python3"):
        real = shutil.which(tool)
        assert real, f"{tool} must exist on PATH for the provisioning script to run"
        (bindir / tool).symlink_to(real)
    monkeypatch.setenv("PATH", str(bindir))
    # Fail loudly rather than silently testing nothing.
    assert shutil.which("herdr") is None, "herdr is still reachable; the guard would be vacuous"
    return bindir


@pytest.fixture
def fleet(tmp_path):
    """A fake suite root with a couple of known package dirs."""
    root = tmp_path / "fleet"
    root.mkdir()
    return root
