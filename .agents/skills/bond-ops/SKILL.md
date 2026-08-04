---
name: bond-ops
description: Maintain the PROJECT BOND fleet-operations package (QUARTERMASTER): inventory, gates, health, provisioning.
version: 1.0.0
author: activeinference.institute
license: MIT
tags: [project-bond, fleet-ops, quality-gates, thin-orchestrator]
---

# bond-ops

Project-scoped skill for the in-repo fleet-operations package at
`projects/working/bond/bond-ops/` (PROJECT BOND Layer 4 · codename
**QUARTERMASTER**). Load this when working inside the package.

## When to Use

- Building/maintaining `bond-ops`: inventory, aggregate gates, per-repo
  health, provisioning, and the `ops` CLI.
- Verifying the package against the shared BOND guardrail preamble (≥90%
  coverage, no mocks, thin orchestrators, no lineage residue).

## Quick Reference

```bash
cd projects/working/bond/bond-ops
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90

# ops CLI (thin)
uv run python scripts/ops_gate.py inventory
uv run python scripts/ops_gate.py gate --json
uv run python scripts/ops_gate.py health
uv run python scripts/ops_gate.py roster

# manuscript tokens
uv run python scripts/z_generate_manuscript_variables.py
```

## Architecture

- `src/bond_ops/inventory.py` — 33-slug roster as data + `reconcile()`.
- `src/bond_ops/gates.py` — one-package-per-subprocess gate + JSON manifest.
- `src/bond_ops/health.py` — git health, required files, lineage sweep.
- `src/bond_ops/provision.py` — herdr roster (read-only by default).
- `src/bond_ops/manuscript_variables.py` — `{{TOKEN}}` map.
- `scripts/` — thin argv wrappers only.

## Pitfalls

- **One package per subprocess in the gate.** Never batch multiple packages
  into a single pytest process (conftest collisions).
- **No mocks.** Use real `tmp_path` fake packages (real src/tests) and real
  `git` repos; drive gates with `sys.executable -m pytest … -p no:cacheprovider`.
- **Safe by default.** `provision` executes nothing without `--execute`.
- **Lineage sweep** is zero-tolerance for the exemplar lineage marker
  (spelled ``template[_]code_project`` in prose); bracket-split the token
  anywhere this repo must mention it, so the doc cannot trip its own sweep.
- **No `infrastructure.*` / sibling imports** in `src/bond_ops/` (stdlib +
  subprocess + PyYAML only).
- **Manuscript tokens** come from `manuscript/config.yaml` +
  `src/bond_ops/manuscript_variables.py`; fleet gate results are runtime
  diagnostics, never hand-authored metrics.

## Cross-refs

- Shared guardrail preamble + BOND suite map: `software-development/bond-suite-package-development` skill.
- Suite roster/scope: `projects/working/bond/` (`SCOPE.md`, `ROSTER.md`).
- Project context: `AGENTS.md`, `docs/agent_instructions.md`.
