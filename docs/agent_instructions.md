# AI Agent Instructions — bond-ops (QUARTERMASTER)

Read this file before touching any other file in this package.

## Why this file exists

`bond-ops` is the Layer-4 fleet-operations package of PROJECT BOND. It owns
the canonical suite roster as data, runs per-package quality gates, reports
fleet health, and emits provisioning commands. Deviating from the rules below
breaks the fleet tooling and misleads whoever maintains the suite.

---

## Rule 1: Scope is exactly this directory

Work **only** inside `projects/working/bond/bond-ops/`. Do not edit sibling
packages, `bond/` root files, or the template repo. Commits are
path-scoped inside this package's own git repo. This tree is **local-only** —
there is no remote, never push.

## Rule 2: Coverage gate — ≥90% on `src/`

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live test count + coverage % live in `docs/_generated/COUNTS.md` — do not
hardcode either number in prose.

## Rule 3: Thin orchestrators

Business logic lives in `src/bond_ops/`; `scripts/` parses argv and prints
only. A line of fleet logic (running a gate, reconciling the roster, sweeping
for lineage) belongs in `src/` where it is covered by tests.

## Rule 4: No mocks; real subprocess + real files

Tests must use real `tmp_path` fake packages (real `src` modules, real
`tests`, exercised via `sys.executable -m pytest …`) and real `git` repos.
No `MagicMock`, `mocker.patch`, or `unittest.mock` anywhere.

## Rule 5: One package per subprocess in the aggregate gate

The gate runs `pytest --cov=src --cov-fail-under=90` **once per package** in
its own subprocess. Never batch multiple packages into a single pytest process
(conftest collisions). See `src/bond_ops/gates.py`.

## Rule 6: Safe by default

Provisioning starts nothing on its own. `ops roster` prints the herdr
commands; execution requires an explicit `--execute`. Gate manifests are
runtime diagnostics, not committed metrics.

## Rule 7: No lineage residue

Aim for zero literal `template[_]code_project` strings. When this doc must
reference the exemplar lineage, bracket-split the token
(`template[_]code_project`) so the doc cannot trip its own sweep.

## Verification checklist (before you say done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
git status --short   # clean after the path-scoped commit
```
