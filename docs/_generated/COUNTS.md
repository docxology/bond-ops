# COUNTS.md — bond-ops live measured evidence

Generated from an actual gate run. Do not hand-edit; re-run the commands below
and replace the values with what they printed.

- **Test count:** 119 passed, 0 failed, 0 skipped
- **Coverage (`src/`, line + branch):** 100.00 %
- **Statements missed:** 0 · **Partial branches:** 0
- **Coverage pragmas in `src/bond_ops/`:** 0

## Per-module coverage

| Module | Stmts | Miss | Branch | BrPart | Cover |
|---|---:|---:|---:|---:|---:|
| `src/bond_ops/cli.py` | 124 | 0 | 26 | 0 | 100.00% |
| `src/bond_ops/figures.py` | 102 | 0 | 18 | 0 | 100.00% |
| `src/bond_ops/gates.py` | 150 | 0 | 36 | 0 | 100.00% |
| `src/bond_ops/health.py` | 122 | 0 | 30 | 0 | 100.00% |
| `src/bond_ops/inventory.py` | 62 | 0 | 8 | 0 | 100.00% |
| `src/bond_ops/manuscript_variables.py` | 42 | 0 | 6 | 0 | 100.00% |
| `src/bond_ops/provision.py` | 56 | 0 | 14 | 0 | 100.00% |
| **TOTAL** | **658** | **0** | **138** | **0** | **100.00%** |

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
