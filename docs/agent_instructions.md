# AI Agent Instructions — bond-ops (QUARTERMASTER)

Read this file before touching any other file in this package.

## Why this file exists

`bond-ops` is the Layer-4 fleet-operations package of PROJECT BOND. It owns the
canonical 33-slug suite roster as data, runs the per-package quality gates,
reports per-repo health, and renders herdr provisioning. Because the rest of
the fleet is judged by output produced here, a defect in this package does not
just break a tool — it produces a *confident wrong answer* about 32 other
packages. The rules below exist to make that hard.

---

## Rule 1: Scope is exactly this directory

Work **only** inside `projects/working/bond/bond-ops/`. Never edit a sibling
package, a `bond/` root file, or the template repo — even when the fleet gate
shows a sibling failing. Reporting a sibling failure is this package's job;
fixing it is not.

Commits are path-scoped inside this package's own git repo. This tree is
**local-only** — there is no remote, and nothing is ever pushed.

## Rule 2: Coverage gate — ≥90% on `src/`

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Line + branch. The live test count and coverage percentage belong in
`docs/_generated/COUNTS.md`; do not hardcode either number in prose anywhere
else, including this file.

## Rule 3: Thin orchestrators

Business logic lives in `src/bond_ops/`; `scripts/` parses argv and prints.
Any line of fleet logic — running a gate, reconciling the roster, sweeping for
lineage, rendering a figure — belongs in `src/`, where the coverage gate can
see it. This is why the argparse surface itself lives in `src/bond_ops/cli.py`
and `scripts/ops_gate.py` is a six-line bootstrap.

## Rule 4: No mocks; real subprocess, real files

Tests use real `tmp_path` packages (real `src` modules, real `tests`, executed
via `sys.executable -m pytest …`), real `git` repositories, and real shell
scripts named `uv` / `herdr` on an override `PATH`. No `MagicMock`,
`mocker.patch`, or `unittest.mock` anywhere. `monkeypatch` may redirect `PATH`
or an environment variable at a real artefact; it may never replace a function
or a return value. Details in `testing_philosophy.md`.

## Rule 5: One package per subprocess in the aggregate gate

The gate runs `pytest --cov=src --cov-fail-under=90` **once per package**, in
its own subprocess, with `cwd` set to that package. Never batch multiple
packages into a single pytest process: scaffold `conftest.py` files mutate
`sys.path` and collide. See `src/bond_ops/gates.py`.

## Rule 6: Safe by default; filters may never widen

Every default path is read-only. `ops roster` prints the herdr commands;
execution requires an explicit `--execute`. Gate manifests are runtime
diagnostics written to `output/`, not committed metrics.

A corollary that has already bitten once: a selection filter must never fail
*open*. `--limit 0` gates nothing and a negative limit is a usage error,
because the earlier "non-positive means no limit" behaviour turned a mistyped
bound into a full-fleet run. If you add a filter, make the degenerate case
select less, never more.

## Rule 7: Verdicts are frozen; diagnostics may widen

`HealthReport.healthy` and `PackageGateResult.passed` are contracts that
`ops health --json` and `ops gate --json` consumers read. Adding a new probe is
welcome; folding it into an existing verdict silently reclassifies packages
that never changed. Add the probe as its own field (as `layout_ok` was) and
leave the verdict alone.

## Rule 8: No lineage residue

Zero literal `template[_]code_project` strings. When a doc must reference the
exemplar lineage, bracket-split the token (`template[_]code_project`) so the
doc cannot trip its own sweep. `src/bond_ops/health.py` builds the marker by
concatenation for the same reason.

## Rule 9: Manuscript numbers come from code

Never type a number into manuscript prose. Identity tokens come from
`manuscript/config.yaml`; every other token is derived from a live constant in
`src/bond_ops/`. Adding a token means editing **both**
`manuscript_variables.build_tokens` and the `tokens:` list in
`manuscript/config.yaml` — a test asserts the two sets are equal. Measured
values (coverage %, test counts) are never tokens; they are runtime
diagnostics.

---

## Verification checklist (before you say done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
uv run python scripts/ops_gate.py health --json | head -30   # self-report is sane
git status --short                                           # clean after the commit
```

`uv` cannot write its cache under a restrictive sandbox. A `Failed to
initialize cache` error is an environment restriction, not a package failure —
re-run with the sandbox disabled. Do not "fix" it by weakening a gate.
