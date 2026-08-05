# docs/ — AGENTS.md

Reading order for an agent arriving in this package:

1. [`agent_instructions.md`](agent_instructions.md) — the rules that govern
   every change here.
2. [`architecture.md`](architecture.md) — what each `src/bond_ops/` module
   does, the import DAG, and why `bond-ops` deliberately ships no `mission.py`.
3. [`testing_philosophy.md`](testing_philosophy.md) — zero mocks, real
   subprocesses, real files, and the determinism rules.

See [`README.md`](README.md) for the full doc inventory, including the doc
surfaces that live outside this directory (package root, per-directory
`AGENTS.md` files, `manuscript/SYNTAX.md`).

Live measured counts (test count, coverage %) are generated under
[`_generated/COUNTS.md`](_generated/COUNTS.md). Do not hardcode them in prose
here or anywhere else; quote the gate command instead.
