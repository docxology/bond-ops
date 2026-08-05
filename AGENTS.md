# AGENTS.md — bond-ops (PROJECT BOND · QUARTERMASTER)

Operational rules for AI agents and developers working inside
`projects/working/bond/bond-ops/`. Read [`docs/agent_instructions.md`](docs/agent_instructions.md)
first, then [`docs/architecture.md`](docs/architecture.md).

## Layer contract

| Surface | Rule |
|---|---|
| `src/bond_ops/` (business logic) | Standard library + `subprocess`, plus PyYAML for manuscript config and matplotlib for figures. **No imports from other BOND packages, no `infrastructure.*`.** Deterministic; side-effect-free except where a subprocess is the point. |
| `scripts/` | Thin orchestrators only (argparse bootstrap + dispatch + printing). Business logic stays in `src/` — including the argparse surface itself, which lives in `src/bond_ops/cli.py` so the coverage gate can see it. |
| `tests/` | Real subprocesses, real git repos, real files. **Zero mocks** (no `MagicMock` / `mocker.patch` / `unittest.mock`). `monkeypatch` may redirect `PATH` or an env var at a real artefact; it may never replace a function or return value. |
| Scope | Exactly this package directory. Never edit siblings, `bond/` root files, or the template repo — not even a sibling the fleet gate reports as failing. |
| Publishing | Local-only tree — there is **no remote**; never push. |

## Build and test

```bash
uv sync --extra dev                       # install (dev extra brings pytest/ruff/mypy)

uv run pytest tests/ --cov=src --cov-fail-under=90     # full gate
uv run pytest tests/test_gates.py -v                   # one module
uv run pytest tests/ -k real_fleet -v                  # the live self-gate only

uv run python scripts/ops_gate.py inventory            # fleet roster vs disk
uv run python scripts/ops_gate.py gate --only bond-ops # gate one package
uv run python scripts/ops_gate.py health --json        # per-repo probes
uv run python scripts/ops_gate.py roster               # provisioning, read-only

uv run python scripts/z_generate_manuscript_variables.py   # -> output/variables/
uv run python scripts/z_generate_figures.py                # -> output/figures/
```

`uv` cannot write `~/.cache/uv` under a restrictive sandbox. `Failed to
initialize cache` is an environment restriction, not a package failure — re-run
outside the sandbox rather than weakening a gate.

## Hard guardrails

- ≥90% **line + branch** coverage on `src/`. Enforced twice: the
  `--cov-fail-under=90` flag and `fail_under` in `[tool.coverage.report]`.
- **No coverage pragmas.** There are none in `src/bond_ops/`, and that is
  *enforced* by `tests/test_guardrails.py::test_no_coverage_pragmas_in_src`
  rather than asserted here. Adding one is a claim that a path cannot be
  reached from a test, and needs to be argued rather than typed. The other way
  to hide a line — `exclude_lines` in `[tool.coverage.report]` — is pinned to
  its three standard regexes by a companion test; the only line they currently
  hide is `cli.py`'s `if __name__ == "__main__":` entrypoint guard.
- Deterministic: fixed inputs, no untracked RNG, and **no wall-clock in any
  persisted artifact**. Gate manifests, roster reports and token maps embed no
  timestamp, so they are byte-identical for a given suite state.
- One package per pytest subprocess in the aggregate gate — never all packages
  in a single pytest process (conftest `sys.path` collisions).
- **Filters fail closed.** `--limit 0` gates nothing; a negative limit is a
  usage error. A degenerate filter value must select less, never more.
- **Verdicts are frozen, diagnostics may widen.** `HealthReport.healthy` and
  `PackageGateResult.passed` are contracts consumed via the JSON manifests. Add
  a new probe as its own field (as `layout_ok` was); do not fold it into an
  existing verdict.
- No leftover `template[_]code_project` strings. When referencing the exemplar
  lineage in a doc, bracket-split the token so the doc cannot trip its own
  sweep.
- Manuscript tokens are injected from `manuscript/config.yaml` +
  `src/bond_ops/manuscript_variables.py` — never hand-author a number in prose.
  A new token must be added to **both** `build_tokens()` and the `tokens:` list
  in `config.yaml`; a test asserts the two sets are equal.
- Live measured counts live in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md);
  do not hardcode test totals or coverage percentages anywhere else.

## Verification before done

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
git status --short   # clean after the path-scoped commit
```

Commit with path-scoped commits inside this repo only (`git add -A` here).

## Suite context

- `bond-ops` sits at Layer 4 alongside `bond-cli`. It imports **nothing** from
  the suite: the 33-slug roster is carried here as data
  (`src/bond_ops/inventory.py`), and the integration point for consuming a
  shared `bond-coordinator` registry is recorded in `TODO.md`.
- It ships **no `mission.py` and no `MissionProvider`** — deliberately. The
  protocol belongs to `bond-api` and is implemented by the 27 film packages;
  the gate runner must not be a member of the population it grades. Rationale
  in `docs/architecture.md` and `README.md`.
- What it publishes for siblings is the versioned JSON manifest set:
  `bond-ops-inventory`, `bond-ops-gate`, `bond-ops-health`, `bond-ops-roster`.
- Subprocess `env` override: `run_command` / `gate_one` / `run_aggregate_gate`
  accept an optional `env` (default `None` inherits), letting a nested gate
  target a sibling's own project environment without touching global state.
