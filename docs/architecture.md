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
- `src/bond_ops/gates.py` — subprocess runners + manifest/report builders.
- `src/bond_ops/health.py` — git/fs inspection (subprocess + reads).
- `src/bond_ops/provision.py` — command generation + safe execution.
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
through the venv interpreter.

## Defaults are read-only

`provision.execute_commands(dry_run=True)` by default records commands without
launching them. Launching requires an explicit flag (`--execute`).

## Adding a new fleet check

1. Add the pure logic (parse + result dataclass) to the relevant `src/bond_ops/` module.
2. Add/route it through the `ops` CLI in `scripts/ops_gate.py` as a thin subcommand.
3. Cover it with a real-filesystem subprocess test.
