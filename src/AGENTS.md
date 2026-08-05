# src/bond_ops/ — Business Logic

All importable fleet-operations logic lives here. `scripts/` remains thin.

## Module map

| Module | Contents |
|---|---|
| `inventory.py` | `PackageRecord`, `ROSTER` (33 records), `SUITE_NAME`, `SUITE_SIZE`/`FILM_COUNT`/`INFRA_COUNT`, `reconcile()`, `package_record()`, `is_known_slug()`, `package_dir()`. |
| `gates.py` | `run_command()`, `parse_coverage()`/`parse_coverage_failure()`/`coverage_stats()`, `gate_one()`, `run_aggregate_gate()`, `AggregateGateReport` (+`coverage_values`, `failed_slugs`), `build_manifest()`/`manifest_to_json()`/`write_manifest()`/`parse_manifest()`, `format_report()`. Default commands run one package per subprocess. Public constants `GATE_MANIFEST_NAME`, `COVERAGE_FLOOR`. Optional `env` passthrough on run/gate calls. |
| `health.py` | `git_health()`, `required_files()`, `lineage_sweep()`, `probe_layout()`/`_read_project_name()`, `tool_versions()`, `health()`, `sweep()`, `HealthReport` (+`probes`, `layout_ok`). |
| `provision.py` | `build_roster()`, `resolve_prompt()`, `render_provision_script()`, `format_provision()`, `roster_report()`, `execute_script()` (dry-run default via CLI). |
| `cli.py` | `ops` argparse surface: `inventory`/`gate`/`health`/`roster`, all with `--json` and `--suite-root`; `ops roster --json` emits the roster manifest. |
| `figures.py` | `plot_roster_composition()`, `plot_fleet_health()`, `plot_gate_coverage()`, `plot_gate_verdicts()` — headless-Agg PNG generators, byte-deterministic. |
| `manuscript_variables.py` | `read_identity()`, `build_tokens()`, `generate_variables()`, `load_generated()`. |

## Rules

- **No imports from other BOND packages** and **no `infrastructure.*`**.
  Deps: stdlib + subprocess + PyYAML (config read only).
- Pure helpers (roster, parse, build) are side-effect-free; file/subprocess
  side effects are confined to the explicitly-I/O functions.
- Defaults are safe/read-only: `provision` executes nothing without `--execute`.
- Determinism: roster counts derive from `inventory` constants, never prose.

## Testing

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live test count + coverage %: `docs/_generated/COUNTS.md`.
