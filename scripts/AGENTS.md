# scripts/ — Thin Orchestrators

`scripts/` is argv-facing glue only. All business logic lives in
`src/bond_ops/`. The two entry points:

| Script | Purpose |
|---|---|
| `ops_gate.py` | `ops` CLI — `inventory`, `gate [--json]`, `health [--json]`, `roster [--json]`/`roster --execute`. Parse args + print; delegate to `bond_ops.*`. |
| `z_generate_manuscript_variables.py` | Writes the manuscript `{{TOKEN}}` map to `output/variables/`. |
| `z_generate_figures.py` | Renders the four manuscript figures into `output/figures/` (real self-gate + fleet sweep). |

The scripts self-insert `../src` into `sys.path` so they can be run directly
(`python scripts/ops_gate.py inventory`). Run from the package root.

## Conventions

- One subcommand per concern; `ops gate --json` is the machine-readable surface.
- Defaults are read-only/safe: `ops roster` prints; it does not start agents
  unless `--execute` is given.
- Exit codes: `0` on success / clean gate; `1` when a `gate` verdict fails
  (any present package failed, or nothing was gated at all); `2` on usage
  error (unknown slug, negative `--limit`, argparse misuse).
  `health`, `inventory` and read-only `roster` are **reporting commands and
  always exit `0`**, however many packages they report as unhealthy or
  missing — read the verdict from `--json`, not from `$?`. Pinned by
  `tests/test_cli.py::test_health_exit_code_is_zero_even_when_packages_are_unhealthy`.
  (`roster --execute` is the one exception: it exits `1` if the provisioning
  script fails.)
