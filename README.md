# bond-ops — PROJECT BOND · QUARTERMASTER

Fleet health, aggregate quality gates, and herdr provisioning for the entire
PROJECT BOND suite — 27 film packages plus 6 infrastructure packages, 33 total.

**Manuscript identity:** `BOND-OPS` · codename **QUARTERMASTER** · Layer 4.

This is a **local-only** working tree. There is no remote and nothing is ever
pushed. `bond-ops` owns exactly its own directory and inspects the sibling
suite read-only, to reconcile the roster, run per-package gates, and report
health.

## The concept mapping

Every BOND package is powered by an idea from its film. The infrastructure
packages take their identity from the organisation behind the missions rather
than from any single film, and `bond-ops` is Q-Branch's quartermaster function:
the officer who does not go on the mission, but who signs off that the
equipment works before anyone does. Q issues the gadget and later asks for it
back in pristine order; `bond-ops` issues nothing and runs no mission — it
inventories the fleet, gates every package's tests, inspects every repository,
and reports what would fail before it fails in the field. The recurring
*"now pay attention, 007"* is the operating posture: the quartermaster's
verdict is delivered whether or not the field agent wants to hear it.

That framing has a concrete architectural consequence. A quartermaster who also
ran missions could not be trusted to grade them, so this package implements no
mission logic at all — see "The MissionProvider surface" below.

## Modules

Business logic lives in `src/bond_ops/`; `scripts/` does argv shaping only.

| Module | What it computes |
|---|---|
| `src/bond_ops/inventory.py` | The canonical 33-slug roster as frozen data (one `PackageRecord` per package: slug, kind, title, codename, canon rank, year), the derived `INFRA_COUNT` / `FILM_COUNT` / `SUITE_SIZE` constants, and the pure `reconcile()` that partitions the roster against live directories into present / missing / unexpected. |
| `src/bond_ops/gates.py` | The aggregate gate. Runs `uv run pytest tests/ --cov=src --cov-fail-under=90` plus ruff and mypy **one package per subprocess**, parses coverage from the pytest-cov `TOTAL` table or its failure line, aggregates min/mean/max, and emits a versioned, timestamp-free JSON manifest plus a human table. |
| `src/bond_ops/health.py` | Per-repo health: git state (branch, SHA, clean, modified/untracked via the pure `parse_porcelain`, ahead/behind upstream), required-file presence, a zero-tolerance `template[_]code_project` lineage sweep, layout probes (`pyproject` name vs slug, `tests/`, `src/`), and a `tool_versions()` toolchain probe. |
| `src/bond_ops/provision.py` | The herdr provisioning roster: a `RosterEntry` per package, prompt-file resolution, a deterministic shell script (`workspace create` → pane id → `agent start` → optional `agent prompt`), a machine-readable `roster_report()`, and the only side-effecting call in the package, `execute_script()`. |
| `src/bond_ops/cli.py` | The `ops` argparse surface — `inventory`, `gate`, `health`, `roster` — each with a human and a `--json` form. `COMMANDS` is the single source of truth for the subcommand set. |
| `src/bond_ops/figures.py` | Four deterministic headless-Agg figure generators: roster composition, fleet-health sweep, gate coverage with the floor line, and a gate verdict heatmap. Byte-identical for fixed inputs. |
| `src/bond_ops/manuscript_variables.py` | Hydrates the manuscript `{{TOKEN}}` map — identity from `manuscript/config.yaml`, every other token derived from a live code constant. |
| `scripts/ops_gate.py` | Thin `ops` CLI bootstrap. |
| `scripts/z_generate_figures.py` | Thin wrapper rendering the four figures into `output/figures/`. |
| `scripts/z_generate_manuscript_variables.py` | Thin wrapper writing the token map to `output/variables/`. |

## Install and run

```bash
# from this package directory
uv sync --extra dev

# Fleet inventory — reconcile the 33-slug roster against live directories
uv run python scripts/ops_gate.py inventory
uv run python scripts/ops_gate.py inventory --json

# Aggregate gate (one subprocess per package); --only / --limit scope it
uv run python scripts/ops_gate.py gate --only bond-utilities,bond-api
uv run python scripts/ops_gate.py gate --json

# Per-repo health: git + required files + lineage + layout probes
uv run python scripts/ops_gate.py health
uv run python scripts/ops_gate.py health --json

# herdr provisioning roster (read-only; nothing starts without --execute)
uv run python scripts/ops_gate.py roster
uv run python scripts/ops_gate.py roster --json

# Manuscript artifacts
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/z_generate_figures.py
```

The installed console script `ops` is the same entry point as
`scripts/ops_gate.py`; either spelling works.

Exit codes: `0` success, `1` a failed gate verdict, `2` usage error (unknown
slug, negative `--limit`, argparse misuse).

## The MissionProvider surface

**There is none, and that is the design.** `bond-ops` ships no `mission.py`,
implements no `bond_api.protocol.MissionProvider`, declares no `GADGETS`
registry, and imports nothing from `bond-api` or any other sibling package.

The `MissionProvider` protocol (`film`, plus `brief` / `recon` / `plan` /
`execute` / `debrief`) is defined by `bond-api` and implemented by the 27 film
packages, which `bond_api.discovery` finds via their `mission` modules.
`bond-ops` is the instrument that measures whether those packages hold up, not
one of the things being measured: making the gate runner a mission provider
would fold it into its own population, so the aggregate gate would gate itself
as a peer and a provider fault would become indistinguishable from a gate fault.

To this package, every slug in the suite — film or infrastructure — is
identically a directory with tests to run, a git tree to inspect, and a layout
to probe. What it *does* publish for siblings to consume is the versioned
`bond-ops-gate`, `bond-ops-health`, `bond-ops-inventory` and `bond-ops-roster`
JSON manifests.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
```

The coverage floor is 90% line+branch on `src/`, enforced by both the
`--cov-fail-under` flag and `fail_under` in `pyproject.toml`. The *measured*
test count and coverage percentage are recorded in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and are deliberately
not quoted here — a number in prose goes stale without anything failing.

If `uv` reports `Failed to initialize cache`, that is a sandbox restriction on
`~/.cache/uv`, not a package failure; re-run outside the sandbox.

## Documentation

- [`docs/`](docs/) — the operational rulebook: `agent_instructions.md` (rules
  for changing anything), `architecture.md` (module-by-module design and the
  import DAG), `testing_philosophy.md` (the zero-mock doctrine).
- [`AGENTS.md`](AGENTS.md) — layer contract and verification checklist.
- [`TODO.md`](TODO.md) — remaining work only.
- [`manuscript/`](manuscript/) — the design record, with `SYNTAX.md` as the
  authoritative token and formalism registry.
