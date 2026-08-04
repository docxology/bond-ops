# Methodology

## Inventory

`src/bond_ops/inventory.py` carries the **{{SUITE_SIZE}}**-slug roster as data
and reconciles it against live directories, flagging missing or unexpected
packages.

## Aggregate gate

`src/bond_ops/gates.py` runs the canonical per-package gate —
`uv run pytest tests/ --cov=src --cov-fail-under={{COVERAGE_FLOOR}}` — **once
per package in its own subprocess**, plus ruff and mypy. Coverage is parsed from
either the pytest-cov `TOTAL` table or the `... not reached. Total coverage:
X%` failure line, and the report aggregates per-package verdicts into the
machine-readable `{{GATE_MANIFEST}}` manifest: presence, pytest pass/fail,
measured coverage, ruff/mypy verdicts, and summary totals plus coverage
min/mean/max. The manifest embeds no wall-clock timestamp, so it is
byte-identical across runs for an unchanged fleet — a live determinism
property.

## Health

`src/bond_ops/health.py` inspects per-repo git state (clean/dirty, branch,
ahead/behind), required-file presence, a zero-tolerance lineage sweep, and
layout probes (pyproject name matches the slug, `tests/` and `src/` present).
`tool_versions()` reports the toolchain the QUARTERMASTER itself depends on.

## Provisioning

`src/bond_ops/provision.py` emits the herdr provisioning roster and a
deterministic machine-readable roster report (kind and prompt-brief counts),
read-only by default; execution requires an explicit `--execute`.
