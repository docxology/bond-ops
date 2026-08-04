# docs/ — Agent-Facing Documentation Hub

Operational rulebook for `projects/working/bond/bond-ops/`. Every document in
this directory is a constraint, not a suggestion.

| File | Governs |
|---|---|
| `agent_instructions.md` | All modifications (read first). |
| `architecture.md` | File/`src`-`scripts` boundaries, one-package-per-subprocess rule. |
| `testing_philosophy.md` | Test modifications, zero-mock + real-subprocess policy. |
| `_generated/COUNTS.md` | Live measured test count + coverage % (regenerated, never hand-edited). |
