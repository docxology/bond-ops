# testing_philosophy.md — bond-ops (QUARTERMASTER)

`bond-ops` is the package that decides whether every other package in the fleet
is trustworthy. Its own tests therefore have to be the least hand-wavy in the
suite: if the gate runner is proved only against a stubbed subprocess, then a
green fleet report proves nothing about the fleet.

## Zero-mock policy

There is no `MagicMock`, `mocker.patch`, `create_autospec`, or `unittest.mock`
import anywhere in `tests/`.

```bash
rg "unittest\.mock|MagicMock|@patch|create_autospec|mocker\." tests/
```

The reason is specific to this package rather than doctrinal. A mocked
`subprocess.run` asserts that we *called* pytest with the right argv; it says
nothing about whether pytest-cov actually prints a `TOTAL` line we can parse,
whether a coverage failure suppresses that table, whether `git status
--porcelain` looks the way `parse_porcelain` expects, or whether a `bash -c`
script with `set -euo pipefail` aborts where we think it does. Every one of
those is a real behaviour of a real tool. So the tests run the real tool.

`monkeypatch` *is* used, but only ever to point `PATH` or an environment
variable at a real artefact the test just created — never to replace a
function, class, or return value. Environment redirection is isolation; object
substitution is a mock.

## What "real" means here, concern by concern

| Concern | Real substitute |
|---|---|
| Gating a package | `make_package()` writes a genuine package under `tmp_path` — real `src/<mod>/core.py`, real `tests/conftest.py`, real `tests/test_core.py` — then the gate runs `sys.executable -m pytest --cov=src --cov-fail-under=90 -p no:cacheprovider` against it in its own subprocess. Passing, failing, and below-floor variants are separate real packages. |
| The default `uv run …` command path | A real four-line `/bin/sh` script named `uv` on an override `PATH`, which logs its argv and emits either a passing `TOTAL` table or the coverage-failure line. This proves the argv we construct without needing a `uv` project in `tmp_path`. |
| Gate timeout | A real `uv` that runs `sleep 5`, gated with `timeout=1`. The `subprocess.TimeoutExpired` path is genuinely raised and genuinely caught. |
| Gate launch failure | A real nonexistent binary name, producing a real `FileNotFoundError`. |
| Git health | A real `git init`, real commits, real modifications and real untracked files under `tmp_path` to flip clean/dirty. The porcelain reduction is additionally unit-tested through the pure `parse_porcelain`. |
| Inventory reconcile | Empty, partial, and fully-populated `tmp_path` roots, plus the live suite root. |
| Provisioning render | Pure string comparison — no subprocess needed, because rendering is pure. |
| Provisioning execute | A real `herdr` shell script on an override `PATH`: one that satisfies the daemon check and emits the `workspace create` JSON payload, and a chattier variant that writes a transcript to stdout so the CLI's echo branch runs for real. The daemon-absent guard is exercised with no `herdr` on `PATH` at all. |
| Layout probes | Real `pyproject.toml` / `tests/` / `src/` files under `tmp_path`, in both the matching and the name-drift case. |
| Toolchain probe | Real `git` / `uv` / `python` on `PATH`, plus a deliberately nonexistent binary for the `None` branch. |
| Figures | Real PNG files written to `tmp_path`, checked for the PNG magic bytes and for byte-identical output across two renders. |
| Recovery paths | A real malformed `config.yaml`, a real corrupt `manuscript_variables.json`. |
| The live fleet | `tests/test_real_fleet.py` runs the gate runner and the health / layout / toolchain probes against the actual sibling packages under `projects/working/bond/`. |

## The self-gate

`tests/test_real_fleet.py::test_real_fleet_gate_runner_on_self` points the gate
runner at `bond-ops` itself, through the venv interpreter, with real
pytest-coverage, real ruff and real mypy. `--ignore=tests/test_real_fleet.py`
keeps the nested run from recursing into itself; `-p no:cacheprovider` keeps it
from writing cache state. The assertion is not "the runner returned an object"
but "the runner reports this package as passing, with a measured coverage at or
above the floor, and a manifest whose summary agrees with the per-package
result".

This is the test that would fail first if the gate machinery ever started
reporting green without running anything.

## Coverage

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Line **and** branch coverage (`branch = true` in `pyproject.toml`), floor 90,
enforced twice — by the `--cov-fail-under` flag and by `fail_under` in
`[tool.coverage.report]`. The live measured value is recorded in
`docs/_generated/COUNTS.md` and quoted nowhere else, because a number in prose
goes stale silently.

If coverage drops, add a test for the uncovered path. Never delete a test, and
never reach for `# pragma: no cover` to make a number move. A pragma is a claim
that a path cannot be reached from a test; each one is a small piece of
untested surface, and a stale pragma sitting on a path that *is* covered is
worse still, because it hides real evidence. There are currently no coverage
pragmas in `src/bond_ops/`.

## Determinism

- **No wall-clock in any persisted artifact.** The gate manifest, the roster
  report, and the manuscript token map embed no timestamp — that is what makes
  the byte-identical assertion across two runs meaningful. (Console output may
  mention durations; nothing written to disk does.)
- **No randomness.** No `random` draws, no set-iteration order leaking into
  output, no dependence on filesystem listing order — `reconcile` sorts its
  unexpected set, and every sweep follows canonical roster order.
- **Figures are byte-checked.** Fixed figure sizes, fixed dpi, Agg backend, and
  `MPLBACKEND=Agg` set in `conftest.py` so no test can open a display.
- **Nested pytest runs pass `-p no:cacheprovider`**, so a child run cannot
  leave cache state that changes a later run.

## Tests that exist to stop other machinery going tautological

Three tests keep independently-maintained artifacts bound to each other. They
are worth protecting during any refactor:

- **The parser-parity test** binds `cli.COMMANDS` to the real argparse
  subparser choices. Without it, `COMMANDS` is a hand-maintained list feeding a
  manuscript token — a number that could drift from reality while still
  "passing".
- **The token-set test** asserts `manuscript/config.yaml`'s declared token list
  equals the keys `build_tokens()` actually produces, so a token can never be
  declared in one place and missing from the other.
- **The formalism cross-reference test** asserts every declared figure, table,
  equation, definition and proposition label is referenced, every reference
  resolves to a declaration, and every citation key exists in `references.bib`
  — so the manuscript cannot ship a dangling `[@ref]`.

Each asserts a relationship between two artifacts that are maintained
separately. A test that only asserts a value against itself proves nothing.
