# bond-ops TODO

Forward-only backlog for the fleet-operations package (PROJECT BOND ·
QUARTERMASTER). No closed-out task archaeology; keep it pointed.

## Phase-3 scope (this build)

- [x] `src/bond_ops/inventory.py` — canonical 33-slug roster as data; reconcile vs live dirs.
- [x] `src/bond_ops/gates.py` — one-package-per-subprocess aggregate gate (`pytest --cov --cov-fail-under=90` + ruff + mypy), JSON manifest + human report.
- [x] `src/bond_ops/health.py` — per-repo git health, required files, lineage sweep.
- [x] `src/bond_ops/provision.py` — informational herdr provisioning roster (read-only by default).
- [x] `scripts/ops_gate.py` — thin `ops` CLI (`inventory` / `gate [--json]` / `health` / `roster`).
- [x] Deterministic test suite (real subprocess, tmp fake packages) at ≥90% coverage.

## Integration points (bind when the sibling lands)

- **Consume a shared suite registry (bond-coordinator).** Today `inventory.py`
  carries the 33-slug roster as data. When `bond-coordinator` exposes a
  machine-readable registry (JSON/YAML/entry-point), reconcile
  `inventory.reconcile` against it and treat mismatches as fleet drift.
  Acceptance: `ops inventory` still shows 33 present with the live fleet, and
  the registry is the single source of truth.
- **Provision agents for real.** `provision.execute_commands` already shells out
  when `--execute` is passed; wire the exact herdr invocation once the fleet
  tab/agent convention is finalised in the suite.

## Quality gates (current evidence)

- Tests + coverage: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
  Live count + coverage % are tracked in `docs/_generated/COUNTS.md`.
- Lint/type: `uv run ruff check src/ scripts/ tests/` and
  `uv run mypy src/ scripts/` must pass clean.
- Lineage: zero `template[_]code_project` hits outside allowed docs.
