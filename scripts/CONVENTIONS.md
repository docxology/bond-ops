# scripts/ — CONVENTIONS

- **Thin only.** A `scripts/` file parses `argv` and prints; it must not
  re-implement business logic already in `src/bond_ops/`.
- **Business logic goes in `src/bond_ops/`** and is covered by `tests/`.
- **Safe by default.** Anything that starts external processes conservatively
  needs an explicit opt-in flag (`--execute`).
- **Deterministic.** Avoid wall-clock dependencies in output text; timestamps
  belong in runtime manifests, not committed docs.
