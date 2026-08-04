# bond-ops — PROJECT BOND · QUARTERMASTER

Fleet health, aggregate quality gates, and herdr provisioning for the entire
PROJECT BOND suite — 27 film packages plus 6 infrastructure packages (33 total).

**Manuscript identity:** `BOND-OPS` · codename **QUARTERMASTER** · Layer 4.

This is a **local-only** working tree. There is no remote and nothing is ever
pushed. `bond-ops` owns exactly its own directory and inspects the sibling
suite only to reconcile the roster, run per-package gates, and report health.

## What it does

| Module | Responsibility |
|---|---|
| `src/bond_ops/inventory.py` | Owns the canonical 33-slug roster as *data* and reconciles it against live suite directories. |
| `src/bond_ops/gates.py` | Runs the aggregate gate — `uv run pytest tests/ --cov=src --cov-fail-under=90`, plus ruff & mypy — **one package per subprocess** for every present package, and emits a JSON manifest (with per-package verdicts + coverage min/mean/max) + a human report. Coverage parses the `TOTAL` table or the `... not reached. Total coverage: X%` failure line. |
| `src/bond_ops/health.py` | Per-repo git health (clean tree, ahead/behind), required-file presence (README/AGENTS/TODO/pyproject), a zero-tolerance `template[_]code_project` lineage sweep, **layout probes** (pyproject-name-vs-slug drift, `tests/`/`src/` present), and a `tool_versions()` toolchain probe. |
| `src/bond_ops/provision.py` | Emits the informational herdr provisioning roster and a deterministic machine-readable roster report (kind + prompt-brief counts). Read-only by default; execution only with an explicit `--execute`. |
| `src/bond_ops/manuscript_variables.py` | Hydrates manuscript `{{TOKEN}}`s from `manuscript/config.yaml` + inventory constants. |
| `scripts/ops_gate.py` | Thin `ops` CLI: `ops inventory`, `ops gate [--json]`, `ops health`, `ops roster`. |
| `scripts/z_generate_manuscript_variables.py` | Thin wrapper writing the manuscript token map to `output/variables/`. |

## Quick usage

```bash
# From this package directory
uv sync --extra dev

# Fleet inventory (reconciles the 33-slug roster against live directories)
uv run python scripts/ops_gate.py inventory

# Aggregate gate, machine-readable manifest
uv run python scripts/ops_gate.py gate --json

# Human gate report
uv run python scripts/ops_gate.py gate

# Per-repo health (git + required files + lineage + layout probes)
uv run python scripts/ops_gate.py health

# Health, machine-readable (per-package probes + layout_ok)
uv run python scripts/ops_gate.py health --json

# Informational herdr provisioning script (read-only; nothing is started)
uv run python scripts/ops_gate.py roster

# Provisioning roster, machine-readable
uv run python scripts/ops_gate.py roster --json
```

The sprinkle of business logic lives in `src/bond_ops/`; `scripts/` keeps to
thin argv shaping. Fleet gate results are **runtime diagnostics**, never
hand-authored manuscript metrics.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ && uv run ruff format src/ scripts/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
```

See `docs/` for the operational rulebook and `TODO.md` for the forward-only
backlog.
