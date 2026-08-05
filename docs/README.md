# docs/ — bond-ops operational documentation

The rulebook for `projects/working/bond/bond-ops/`, the Layer-4 QUARTERMASTER
of PROJECT BOND. Every document here is a constraint on how this package may
change, not background reading.

## What is in here

| File | Governs | Read it when |
|---|---|---|
| [`agent_instructions.md`](agent_instructions.md) | Every modification to this package: scope, coverage gate, thin-orchestrator rule, no-mocks rule, subprocess isolation, safe defaults, lineage hygiene. | Before touching any file. |
| [`architecture.md`](architecture.md) | The module-by-module design of `src/bond_ops/`, the import DAG, the `src`/`scripts` boundary, the one-package-per-subprocess rule, and why there is deliberately no `mission.py` here. | Before adding or moving a module. |
| [`testing_philosophy.md`](testing_philosophy.md) | The zero-mock, real-subprocess, real-filesystem test doctrine and the determinism rules that go with it. | Before writing or changing a test. |
| [`AGENTS.md`](AGENTS.md) | The reading order for the three documents above. | On arrival. |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | The live measured test count and coverage percentage. Regenerated from an actual run — never hand-edited, never quoted in other prose. | When you need the current numbers. |

## Reading order

`agent_instructions.md` → `architecture.md` → `testing_philosophy.md`.

## Where the other docs live

This directory holds the *operational* rules. Three other doc surfaces exist
and are not duplicated here:

- **Package root** — `README.md` (what the package is and how to run it),
  `AGENTS.md` (the layer contract and the verification checklist), `TODO.md`
  (remaining work only), `STANDALONE.md` (the fork contract).
- **Per-directory contracts** — `src/AGENTS.md`, `scripts/AGENTS.md`,
  `tests/AGENTS.md` each state the rule governing that one directory.
- **Manuscript** — `manuscript/SYNTAX.md` is the authoritative registry of the
  `{{TOKEN}}` map and every auto-numbered formalism label;
  `manuscript/AGENTS.md` is the folder contract.

## The one rule that spans all of them

No document in this package states a measured number. Coverage percentages and
test counts live in `_generated/COUNTS.md` and are produced by running the
gate; the manuscript quotes derived constants through `{{TOKEN}}`s hydrated
from code. A hand-typed metric anywhere else is a defect — replace it with the
gate command that produces it.
