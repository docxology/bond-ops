# Experimental Setup {#sec:setup}

- **Runtime.** Python ≥3.10, standard library + `subprocess` + `pyyaml` +
  `matplotlib` (figures only). No `infrastructure.*` and no sibling BOND
  import.
- **Gate command** invoked per package (one subprocess each): `uv run pytest
  tests/ --cov=src --cov-fail-under={{COVERAGE_FLOOR}}`, killed after
  {{GATE_TIMEOUT_S}} s so a hung package cannot stall the sweep (the timeout is
  recorded as a gate failure with its exception text, never as a pass).
- **Fleet root**: `{{SUITE_NAME}}` at `projects/working/bond/`,
  {{SUITE_SIZE}} packages ({{INFRA_COUNT}} infra, {{FILM_COUNT}} films).
- **Isolation contract**: each gate subprocess runs with `cwd` equal to the
  package's own directory; never all packages in one pytest process
  ([@prop:isolation]).
- **Figures**: rendered headlessly (Agg) into `output/figures/` by
  `scripts/z_generate_figures.py`, byte-deterministic for fixed inputs.

The toolchain is pinned via `uv.lock` ([@tbl:toolchain]).

| Tool | Role |
|---|---|
| pytest | test framework for every fleet package gate |
| pytest-cov | line+branch coverage at the {{COVERAGE_FLOOR}}% floor |
| ruff | lint + format in the aggregate gate |
| mypy | static type check in the aggregate gate |
| uv | environment + lockfile management |
: The QUARTERMASTER toolchain. {#tbl:toolchain}

The package's own test suite exercises the real subprocess machinery against
deterministic tmp-path fake packages (and a fake `uv`/`herdr` on `PATH`), with
zero mocks, and must hold ≥{{COVERAGE_FLOOR}}% line+branch coverage on `src/` (enforced by
`--cov-fail-under={{COVERAGE_FLOOR}}` and the pyproject `fail_under`). A
dedicated real-fleet test module additionally runs the gate runner and the
health/layout probes against the live sibling packages under
`projects/working/bond/`, giving the QUARTERMASTER an end-to-end gate it can
trust on the fleet it operates.
