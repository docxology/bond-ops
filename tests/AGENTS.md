# tests/ — Test Suite

## Key Concepts

- **Zero-mock policy**: every interaction is a real subprocess or real file.
  Fake *packages* are real directories with real `src` modules and real tests
  (see `conftest.py::make_package`); git state is exercised through real
  `git` commits in `tmp_path` repos.
- **Deterministic**: no mock frameworks (`MagicMock`/`mocker.patch`/
  `unittest.mock`), fixed inputs, `-p no:cacheprovider` for nested pytest runs.
- **Coverage gate**: `uv run pytest tests/ --cov=src --cov-fail-under=90`
  (live count + % in `docs/_generated/COUNTS.md`).

## Test modules

| Module | Covers |
|---|---|
| `test_inventory.py` | 33-slug roster, kind split, reconcile vs live dirs + tmp roots. |
| `test_gates.py` | subprocess gate (`gate_one`) pass/fail/coverage, `TOTAL`-or-failure-line coverage parse, coverage stats, ruff/mypy, manifest JSON, report. |
| `test_health.py` | real git repos: clean/dirty/untracked, required files, lineage sweep, layout probes, toolchain probe. |
| `test_provision.py` | herdr provisioning lines/script, dry-run vs real execution, roster report. |
| `test_manuscript_variables.py` | token hydration, malformed-config and corrupt-token-file recovery, token values bound to live code constants, and `config.yaml`-vs-`build_tokens()` set equality. |
| `test_manuscript_formalisms.py` | auto-numbered formalism registry: every declared fig/tbl/eq/def/prop referenced, every reference resolves, every citation key in `references.bib`. |
| `test_figures.py` | headless-Agg PNG generators: magic bytes, non-trivial size, byte-determinism, empty-data guards. |
| `test_cli.py` | in-process `ops` CLI: every subcommand, `--json` manifests, human tables, exit codes, `--limit` bounds, and `COMMANDS`-vs-parser parity. |
| `test_real_fleet.py` | gate runner + health/layout/toolchain probes against the live fleet. |
| `test_scripts_smoke.py` | subprocess smoke of `ops` CLI and the variables script. |

## Helpers

`conftest.py` exposes:

- `make_package(root, slug, *, failing=False, cov_low=False)` — real fake package.
- `fake_uv` / `fake_herdr` fixtures — real executable shell scripts on an
  override `PATH` that log argv and emit canned coverage/`workspace` JSON.
- `fleet` fixture — an empty tmp dir standing in for the live suite root.

Nested pytest runs use `sys.executable -m pytest tests/ --cov=src --cov-fail-under=90
-p no:cacheprovider` so each fake package is gated exactly like the real fleet
(one package per subprocess), just against the venv interpreter.
