# Results {#sec:results}

The fleet surface produced by {{PACKAGE_NAME}} (codename {{CODENAME}}), all
measured from real subprocess and filesystem state:

- **Inventory.** `ops inventory` reconciles the canonical roster
  ([@def:suite-roster]) against `projects/working/bond/` and reports present,
  missing, and unexpected directories. A complete fleet shows `present
  {{SUITE_SIZE}}/{{SUITE_SIZE}} · complete yes` ([@eq:reconcile-verdict]).
- **Aggregate gate.** `ops gate --json` emits a deterministic
  `{{GATE_MANIFEST}}` manifest ([@def:aggregate-gate]) containing, for each
  package, its presence, pytest pass/fail, measured coverage, ruff and mypy
  verdicts, and the summary totals with coverage min/mean/max over the
  {{COVERAGE_FLOOR}}-floor gate ([@eq:coverage-mean], [@eq:coverage-extrema],
  [@eq:gate-verdict]). `ops gate` (human form) prints a per-package table; the
  exit code is `0` iff every present package passes.
- **Fleet health.** `ops health` reports per-repo clean/dirty, branch,
  ahead/behind, required-file coverage, lineage hits, layout probes, and the
  overall verdict ([@def:health-verdict]); `--json` exposes `probes` and
  `layout_ok` per package. [@fig:fleet-health] shows a real sweep over the
  whole fleet.
- **Provisioning roster.** `ops roster` prints the herdr provisioning script;
  `ops roster --json` emits a machine-readable roster report
  ([@def:provisioning-roster]); `ops roster --execute` runs it against the
  herdr daemon.

The gate manifest schema (version 1) is summarised in [@tbl:gate-manifest].

| Field | Type | Meaning |
|---|---|---|
| `manifest` | string | manifest identifier (`{{GATE_MANIFEST}}`) |
| `schema_version` | integer | schema version (1) |
| `generated_by` | string | fleet identity (`{{CODENAME}}`) |
| `suite` | string | suite name (`{{SUITE_NAME}}`) |
| `summary` | object | totals (present / passed / failed / missing) + coverage measured / mean / min / max |
| `packages` | array | per-package verdict objects (presence, pytest / ruff / mypy, coverage) |
: The `{{GATE_MANIFEST}}` manifest schema, version 1. {#tbl:gate-manifest}

![Fleet health across the whole roster: one row per package, green = healthy, red = unhealthy, grey = missing.](../output/figures/fleet_health.png){#fig:fleet-health width=75%}

![Measured gate coverage with the {{COVERAGE_FLOOR}}% floor reference line.](../output/figures/gate_coverage.png){#fig:gate-coverage width=60%}

![Aggregate gate verdict heatmap (pytest / ruff / mypy / passed).](../output/figures/gate_verdicts.png){#fig:gate-verdicts width=60%}

Because the manifest carries no wall-clock timestamp and asks only real
processes for their verdicts, re-running `ops gate` against an unchanged fleet
yields an identical manifest — a live determinism check
([@prop:manifest-determinism]).
