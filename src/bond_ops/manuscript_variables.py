"""Manuscript variable hydration for bond-ops.

Builds the ``{{TOKEN}}`` substitution map referenced by the manuscript prose.
Identity tokens (package name, codename) come from ``manuscript/config.yaml``;
roster-derived tokens come from the deterministic suite constants in
``inventory.py``. No metrics are hard-authored — fleet gate results are
runtime diagnostics, not manuscript tokens.

The output JSON is written under ``output/variables/manuscript_variables.json``
so a static cross-reference test can verify that every ``{{TOKEN}}`` appearing
in the numbered prose sections is generated here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import yaml

from .gates import COVERAGE_FLOOR, GATE_MANIFEST_NAME
from .inventory import (
    BOND_OPS_CODENAME,
    FILM_COUNT,
    INFRA_COUNT,
    SUITE_NAME,
    SUITE_SIZE,
)

#: Defaults used when ``manuscript/config.yaml`` is absent (tests, drafts).
_DEFAULT_IDENTITY = {
    "package_name": "bond-ops",
    "codename": BOND_OPS_CODENAME,
}


def read_identity(project_root: str | Path) -> dict[str, str]:
    """Read the manuscript identity (package name + codename) from
    ``manuscript/config.yaml`` when present, else return defaults."""
    config_path = Path(project_root) / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return dict(_DEFAULT_IDENTITY)

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):  # pragma: no cover - unreadable/malformed
        return dict(_DEFAULT_IDENTITY)

    if not isinstance(raw, dict):
        return dict(_DEFAULT_IDENTITY)
    return {
        "package_name": str(
            (raw.get("package") or {}).get("name") or _DEFAULT_IDENTITY["package_name"]
        ),
        "codename": str(
            (raw.get("package") or {}).get("codename") or _DEFAULT_IDENTITY["codename"]
        ),
    }


def build_tokens(project_root: str | Path) -> dict[str, str]:
    """Return the full ``{{TOKEN}}`` → value map for the manuscript."""
    identity = read_identity(project_root)
    return {
        "SUITE_NAME": SUITE_NAME,
        "PACKAGE_NAME": identity["package_name"],
        "CODENAME": identity["codename"],
        "SUITE_SIZE": str(SUITE_SIZE),
        "FILM_COUNT": str(FILM_COUNT),
        "INFRA_COUNT": str(INFRA_COUNT),
        "GATE_MANIFEST": GATE_MANIFEST_NAME,
        "COVERAGE_FLOOR": str(COVERAGE_FLOOR),
    }


def generate_variables(
    project_root: str | Path, *, require_analysis_outputs: bool = False
) -> dict[str, str]:
    """Generate the token map and persist it to
    ``output/variables/manuscript_variables.json``.

    ``require_analysis_outputs`` is accepted for contract parity with sibling
    packages but bond-ops identity tokens are data-derived and never require a
    prior analysis run, so it has no effect on the non-empty token set.
    """
    del require_analysis_outputs  # identity tokens need no analysis outputs
    tokens = build_tokens(project_root)
    out_dir = Path(project_root) / "output" / "variables"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manuscript_variables.json").write_text(
        json.dumps(tokens, indent=2, sort_keys=True), encoding="utf-8"
    )
    return tokens


def load_generated(project_root: str | Path) -> dict[str, str]:
    """Read back the generated token map from disk, or ``{}`` if absent."""
    path = Path(project_root) / "output" / "variables" / "manuscript_variables.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # pragma: no cover - corrupt file
        return {}
    payload = cast("dict[str, object]", data)
    return {str(k): str(v) for k, v in payload.items() if isinstance(v, (str, int, float))}
