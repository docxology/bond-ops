# architecture.md — bond-ops

## Layers

```
scripts/             thin CLI (argv -> print)   [no business logic]
   |
   v
src/bond_ops/        business logic (stdlib + subprocess + PyYAML)
   |
   v
sibling packages     inspected READ-ONLY (reconcile, gate, health, provision)
```

- `src/bond_ops/inventory.py` — data + pure reconcile functions (no I/O).
- `src/bond_ops/gates.py` — subprocess runners + manifest/report builders
  (coverage `TOTAL`-or-failure-line parse, coverage min/mean/max aggregation).
- `src/bond_ops/health.py` — git/fs inspection (subprocess + reads) + layout
  probes (`probe_layout`) + toolchain probe (`tool_versions`).
- `src/bond_ops/provision.py` — command generation, roster report, safe execution.
- `src/bond_ops/cli.py` — the `ops` argparse surface (in `src/`, not `scripts/`).
- `src/bond_ops/manuscript_variables.py` — `{{TOKEN}}` map for the manuscript.

## Dependency rule

- `src/bond_ops/` imports **only** the standard library, `subprocess`, and
  PyYAML. No `infrastructure.*`, no sibling BOND packages. If a sibling
  (e.g. `bond-coordinator` registry) becomes available, bind via the
  integration point recorded in `TODO.md`, not a hard import.

## One-package-per-subprocess rule

The aggregate gate (`run_aggregate_gate` → `gate_one`) launches
`pytest --cov=src --cov-fail-under=90` once per package, with `cwd` set to the
package's own directory. This isolates conftest/coverage state between
packages. Commands are injectable so tests drive deterministic fake packages
through the venv interpreter. `run_command`/`gate_one`/`run_aggregate_gate`
accept an optional `env` (default `None` inherits) so a nested gate can target
a sibling's own project environment without touching global state.

## Defaults are read-only

Provisioning renders a script and a machine-readable roster report, but
launches nothing on its own. `ops roster`/`ops roster --json` are read-only;
execution requires `--execute` (which shells out via `bash`).

## Real-fleet test

`tests/test_real_fleet.py` gates `bond-ops` itself through the venv
interpreter (real pytest-coverage/ruff/mypy, `--ignore=tests/test_real_fleet.py`
to avoid recursion) and runs health + layout + toolchain probes against real
live siblings, so the QUARTERMASTER is itself verified on the fleet it
operates.

## Adding a new fleet check

1. Add the pure logic (parse + result dataclass) to the relevant `src/bond_ops/` module.
2. Add/route it through the `ops` CLI in `scripts/ops_gate.py` as a thin subcommand.
3. Cover it with a real-filesystem subprocess test.
