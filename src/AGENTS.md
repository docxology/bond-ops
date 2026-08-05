# src/bond_ops/ — Business Logic

All importable fleet-operations logic lives here. `scripts/` remains thin.

## Module map

| Module | Contents |
|---|---|
| `inventory.py` | `PackageRecord`, `ROSTER` (33 records), `SUITE_NAME`, `SUITE_SIZE`/`FILM_COUNT`/`INFRA_COUNT`, `reconcile()`, `package_record()`, `is_known_slug()`, `package_dir()`. |
| `gates.py` | `run_command()`, `parse_coverage()`/`parse_coverage_failure()`/`coverage_stats()`, `gate_one()`, `run_aggregate_gate()`, `AggregateGateReport` (+`coverage_values`, `failed_slugs`), `build_manifest()`/`manifest_to_json()`/`write_manifest()`/`parse_manifest()`, `format_report()`. Default commands run one package per subprocess. Public constants `GATE_MANIFEST_NAME`, `COVERAGE_FLOOR`, `DEFAULT_TIMEOUT`. Optional `env` passthrough on run/gate calls. A malformed `TOTAL` cell falls through to the failure-line parse; `limit=0` selects nothing and a negative limit raises `ValueError`. |
| `health.py` | `parse_porcelain()` (pure), `git_health()`, `required_files()`, `lineage_sweep()`, `probe_layout()`/`_read_project_name()`, `tool_versions()`, `health()`, `sweep()`, `HealthReport` (+`probes`, `layout_ok`). `REQUIRED_FILES` is the public constant. |
| `provision.py` | `build_roster()`, `resolve_prompt()`, `render_provision_script()`, `format_provision()`, `roster_report()`, `execute_script()` (dry-run default via CLI). |
| `cli.py` | `ops` argparse surface: `inventory`/`gate`/`health`/`roster`, all with `--json` and `--suite-root`; `ops roster --json` emits the roster manifest. `COMMANDS` is the single source of truth for the subcommand set (bound to the real parser by a test) and feeds the `CLI_COMMAND_COUNT` token. |
| `figures.py` | `plot_roster_composition()`, `plot_fleet_health()`, `plot_gate_coverage()`, `plot_gate_verdicts()` — headless-Agg PNG generators, byte-deterministic. |
| `manuscript_variables.py` | `read_identity()`, `build_tokens()`, `generate_variables()`, `load_generated()`. Every non-identity token is derived from a live constant in the modules above. |

## Rules

- **No imports from other BOND packages** and **no `infrastructure.*`**.
  Deps: stdlib + subprocess, PyYAML (config read only), matplotlib
  (`figures.py` only, Agg backend). In particular nothing here imports
  `bond-api`: this package ships no `mission.py` and no `MissionProvider`
  by design (see `../docs/architecture.md`).
- **No coverage pragmas.** There are none in this directory, enforced by
  `tests/test_guardrails.py::test_no_coverage_pragmas_in_src` (a sweep, not a
  sentence); adding one is a claim a path is untestable and must be argued.
  The `[tool.coverage.report] exclude_lines` regexes are pinned by a companion
  test and currently hide exactly one line — `cli.py`'s `__main__` guard.
- **Verdicts are frozen, diagnostics may widen.** `HealthReport.healthy` and
  `PackageGateResult.passed` are published manifest contracts; add a new probe
  as its own field instead of folding it in.
- Pure helpers (roster, parse, build) are side-effect-free; file/subprocess
  side effects are confined to the explicitly-I/O functions.
- Defaults are safe/read-only: `provision` executes nothing without `--execute`.
- Determinism: roster counts derive from `inventory` constants, never prose.

## Testing

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live test count + coverage %: `docs/_generated/COUNTS.md`.
