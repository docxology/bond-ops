"""Subprocess smoke tests for the thin scripts/ wrappers (real subprocess)."""

from __future__ import annotations

import json
import subprocess
import sys

from conftest import PROJECT_ROOT


def _run_script(name, *args):
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / name), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=240,
    )


def test_ops_gate_inventory_smoke():
    result = _run_script("ops_gate.py", "inventory", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["manifest"] == "bond-ops-inventory"
    assert data["summary"]["total"] == 33


def test_z_generate_manuscript_variables_smoke():
    result = _run_script("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    out_path = PROJECT_ROOT / "output" / "variables" / "manuscript_variables.json"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["CODENAME"] == "QUARTERMASTER"
