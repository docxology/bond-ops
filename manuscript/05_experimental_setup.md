# Experimental Setup

- **Runtime.** Python ≥3.10, standard library + `subprocess` + `pyyaml`. No `infrastructure.*` and no sibling BOND import.
- **Gate command** invoked per package (one subprocess each): `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- **Toolchain** (dev extras): `pytest`, `pytest-cov`, `ruff`, `mypy`, `types-PyYAML`.
- **Fleet root**: `{{SUITE_NAME}}` at `projects/working/bond/`, {{SUITE_SIZE}} packages ({{INFRA_COUNT}} infra, {{FILM_COUNT}} films).
- **Isolation contract**: each gate subprocess runs with `cwd` equal to the package's own directory; never all packages in one pytest process.

The package's own test suite exercises the real subprocess machinery against deterministic tmp-path fake packages (and a fake `uv`/`herdr` on `PATH`), with zero mocks, and must hold ≥90% line+branch coverage on `src/` (enforced by `--cov-fail-under=90` and the pyproject `fail_under`).
