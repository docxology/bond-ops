# testing_philosophy.md — bond-ops

## Zero-mock policy

Every test exercises **real** computation, **real** subprocesses, and **real**
files. There is no `MagicMock`, `mocker.patch`, `create_autospec`, or
`unittest.mock` anywhere in `tests/`. Enforcement: `rg "unittest.mock|MagicMock|@patch|create_autospec" tests/`.

Why: a mock test asserts call signatures, not behaviour. `bond-ops` gates the
real fleet; its own tests must prove the real subprocess/fs paths work.

## Real-data strategy

| Concern | Real substitute |
|---|---|
| Package gating | `make_package` → real `src/` module + real `tests/`; run with `sys.executable -m pytest --cov=src --cov-fail-under=90 -p no:cacheprovider` in its own subprocess (or a fake `uv`/`herdr` on an override `PATH` for the default-command path). |
| Git health | real `git init` + commits under `tmp_path`; modify/untrack files to flip state. |
| Inventory reconcile | empty/partial tmp roots → missing/unexpected; the live suite root → present. |
| Provisioning | dry-run (no subprocess) + a real `true`/`false` command for the execute path; a real fake-`herdr` bin for the script-execute path. |
| Layout probes | real `pyproject.toml`/`tests/`/`src/` files under `tmp_path` (name match and drift cases). |
| Toolchain probe | real `git`/`uv`/`python` on PATH (versions verified non-`None`). |
| Real fleet | `tests/test_real_fleet.py` runs the gate runner + health/layout/toolchain probes against the live sibling packages. |

## Coverage

`uv run pytest tests/ --cov=src --cov-fail-under=90` (line+branch). Live
count + % is tracked in `docs/_generated/COUNTS.md`. If coverage drops, add a
test for the uncovered path — never delete tests to make the number pass.

## Determinism

No wall-clock in committed artifacts; timestamps appear only in runtime gate
manifests. Fixed inputs everywhere. Nested pytest runs pass
`-p no:cacheprovider` to avoid cache side effects.
