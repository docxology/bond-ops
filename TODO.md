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

## Phase-4 deepening (this build)

- [x] `gates.py` — coverage parses the pytest-cov `... not reached. Total coverage: X%`
  failure line as a fallback to the `TOTAL` table; `coverage_stats()` helper and
  `coverage_values`/`failed_slugs` on the report; optional per-subprocess `env`
  passthrough (`run_command`/`gate_one`/`run_aggregate_gate`) so a nested gate
  can target a sibling's own project environment.
- [x] `health.py` — `probe_layout()` (pyproject-name-vs-slug drift, `tests/` and
  `src/` presence) with `HealthReport.layout_ok`; `tool_versions()` toolchain
  probe (git/uv/python). `healthy` verdict contract unchanged (probes are
  diagnostic, not folded in).
- [x] `provision.py` — `roster_report()` deterministic machine-readable roster
  manifest (kind + prompt-brief counts); `ops roster --json`.
- [x] `cli.py` — `ops roster --json`; `ops health --json` exposes per-package
  `probes` and `layout_ok`.
- [x] Real-fleet test module (`tests/test_real_fleet.py`) — the gate runner gates
  `bond-ops` itself through the venv interpreter (real pytest-coverage/ruff/mypy,
  `--ignore=tests/test_real_fleet.py` to avoid recursion); health + layout +
  toolchain probes run against real live siblings. 0 mocks, 0 skips.

## Phase-5 manuscript + visualizations (this build)

- [x] `src/bond_ops/figures.py` — deterministic headless-Agg generators:
  `plot_roster_composition` (frozen roster data), `plot_fleet_health` (real
  sweep over all 33), `plot_gate_coverage` (floor line) and `plot_gate_verdicts`
  (pytest/ruff/mypy/passed heatmap). Byte-identical for fixed inputs.
- [x] `scripts/z_generate_figures.py` — thin wrapper rendering the four figures
  into `output/figures/` (gate figures come from a real self-gate).
- [x] Manuscript deepened with **auto-numbered formalisms**: `{#sec:}` section
  labels, `::: {.definition/#prop}` blocks, `{#eq:}` equations, `{#fig:}`
  figures with self-contained captions, `{#tbl:}` tables, `[@key]` citations;
  preamble LaTeX block; SYNTAX.md formalism registry.
- [x] `tests/test_figures.py` (PNG magic + byte-determinism) and
  `tests/test_manuscript_formalisms.py` (every declared formalism referenced,
  every reference resolves, every citation key in `references.bib`).

## Integration points (bind when the sibling lands)

- **Consume a shared suite registry (bond-coordinator).** Today `inventory.py`
  carries the 33-slug roster as data. When `bond-coordinator` exposes a
  machine-readable registry (JSON/YAML/entry-point), reconcile
  `inventory.reconcile` against it and treat mismatches as fleet drift.
  Acceptance: `ops inventory` still shows 33 present with the live fleet, and
  the registry is the single source of truth.

## Provisioning state

`provision.py` renders the herdr provisioning roster per the
`herdr-multiple-hermes-dispatch` skill: `workspace create --label --cwd
--no-focus`, `agent start --kind hermes --timeout 90000`, then a fire-and-forget
`agent prompt` when a prompt file exists. Rendering is pure; `ops roster` prints
it read-only and `ops roster --execute` runs it via a real `bash` subprocess
(covered by tests with a fake `herdr` on PATH).

## Quality gates (current evidence)

- Tests + coverage: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
  Live count + coverage % are tracked in `docs/_generated/COUNTS.md`.
- Lint/type: `uv run ruff check src/ scripts/ tests/` and
  `uv run mypy src/ scripts/` must pass clean.
- Lineage: zero `template[_]code_project` hits outside allowed docs.
