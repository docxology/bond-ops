# src/bond_ops/ — Business Logic

All importable fleet-operations logic lives here. `scripts/` remains thin.

## Module map

| Module | Contents |
|---|---|
| `inventory.py` | `PackageRecord`, `ROSTER` (33 records), `SUITE_NAME`, `SUITE_SIZE`/`FILM_COUNT`/`INFRA_COUNT`, `reconcile()`, `package_record()`, `is_known_slug()`, `package_dir()`. |
| `gates.py` | `run_command()`, `parse_coverage()`, `gate_one()`, `run_aggregate_gate()`, `AggregateGateReport`, `build_manifest()`/`manifest_to_json()`/`write_manifest()`/`parse_manifest()`, `format_report()`. Default commands run one package per subprocess. |
| `health.py` | `git_health()`, `required_files()`, `lineage_sweep()`, `health()`, `HealthReport`. |
| `provision.py` | `build_provision_lines()`, `format_provision()`, `execute_commands()` (dry-run default). |
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
