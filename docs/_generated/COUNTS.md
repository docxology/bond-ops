# COUNTS.md — bond-ops live measured evidence

Generated from an actual gate run. Do not hand-edit; re-run the commands below
and replace the values with what they printed.

- **Test count:** 133 passed, 0 failed, 0 skipped
- **Coverage (`src/`, line + branch):** 100.00 %
- **Statements missed:** 0 · **Partial branches:** 0
- **Coverage pragmas in `src/bond_ops/`:** 0 (swept and enforced by
  `tests/test_guardrails.py::test_no_coverage_pragmas_in_src`, not asserted)

## Per-module coverage

| Module | Stmts | Miss | Branch | BrPart | Cover |
|---|---:|---:|---:|---:|---:|
| `src/bond_ops/cli.py` | 124 | 0 | 26 | 0 | 100.00% |
| `src/bond_ops/figures.py` | 102 | 0 | 18 | 0 | 100.00% |
| `src/bond_ops/gates.py` | 157 | 0 | 38 | 0 | 100.00% |
| `src/bond_ops/health.py` | 126 | 0 | 30 | 0 | 100.00% |
| `src/bond_ops/inventory.py` | 62 | 0 | 8 | 0 | 100.00% |
| `src/bond_ops/manuscript_variables.py` | 42 | 0 | 6 | 0 | 100.00% |
| `src/bond_ops/provision.py` | 56 | 0 | 14 | 0 | 100.00% |
| **TOTAL** | **669** | **0** | **140** | **0** | **100.00%** |

## What the 100% does and does not include

It is measured over every statement and branch coverage.py sees in
`src/bond_ops/`, with **no** `# pragma: no cover` anywhere in the package. The
denominator does exclude one construct: `[tool.coverage.report] exclude_lines`
carries the standard `if __name__ == .__main__.:` regex, which hides `cli.py`'s
two-line entrypoint guard — a block no in-process test can drive. That is the
only production line excluded from measurement by any mechanism here; two tests
in `tests/test_guardrails.py` pin the exclusion list and assert the pattern
matches in `cli.py` and nowhere else.

`health.py` and `gates.py` grew by 4 and 7 statements against the previous
receipt: two formerly-pragma'd `except` branches in `health.py` are now real,
covered code (an unreadable file and an unexecutable binary, both driven with
real files), and `gates.py` gained the wall-clock scrubber.

## How it was measured

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

Environment at time of measurement: Python 3.14.6 (darwin), pytest 9.0.2,
pytest-cov 7.0.0. Ruff check and format clean on `src/`, `scripts/` and
`tests/`; mypy clean on `src/` and `scripts/`.

The run includes `tests/test_real_fleet.py`, which gates this package against
the live sibling tree with real pytest-coverage, ruff and mypy subprocesses, so
the number above is produced by machinery that has itself been exercised
against the real fleet.

The floor enforced by the gate is 90%; the measured value is well above it.
Do not treat the measured value as the contract — the gate is the contract, and
this file is only the receipt.
