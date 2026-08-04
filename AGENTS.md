# AGENTS.md — bond-ops (PROJECT BOND · QUARTERMASTER)

Operational rules for AI agents and developers working inside
`projects/working/bond/bond-ops/`. Read `docs/agent_instructions.md` first.

## Layer contract

| Surface | Rule |
|---|---|
| `src/bond_ops/` (business logic) | Pure stdlib + subprocess logic, plus PyYAML for manuscript config. **No imports from other BOND packages, no `infrastructure.*`.** Deterministic and side-effect-free where possible. |
| `scripts/` | Thin orchestrators only (argparse + dispatch + printing). Business logic stays in `src/`. |
| `tests/` | Real subprocess + real files. **Zero mocks** (no `MagicMock`/`mocker.patch`/`unittest.mock`). |
| Scope | Exactly this package directory. Never edit siblings, `bond/` root files, or the template repo. |
| Publishing | Local-only tree — there is **no remote**; never push. |

## Hard guardrails

- ≥90% line+branch coverage on `src/`: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- Deterministic: fixed seeds / fixed inputs; no untracked RNG; no wall-clock
  in any persisted artifact (gate manifests embed no timestamp — they are
  byte-identical for a given suite state).
- One package per pytest subprocess in the aggregate gate — never all packages
  in a single pytest process (conftest collisions).
- No leftover `template[_]code_project` strings; aim for zero. When referencing
  the exemplar lineage in this doc, bracket-split the token
  (`template[_]code_project`) so the doc cannot trip its own sweep.
- Manuscript tokens are injected from `manuscript/config.yaml` +
  `src/bond_ops/manuscript_variables.py` — never hand-author metrics in prose.
- Live measured counts live in `docs/_generated/COUNTS.md`; do not hardcode
  test totals or coverage % in prose.

## Verification before done

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
git status --short   # clean after the path-scoped commit
```

Commit with path-scoped commits inside this repo only (`git add -A` here).

## Suite context

- `bond-ops` depends on `bond-coordinator` (registry) only for suite
  inventory; today the 33-slug roster is carried here as data
  (`src/bond_ops/inventory.py`) and the integration point to consume a shared
  registry is recorded in `TODO.md`.
- The rest is stdlib + subprocess.
