# STANDALONE.md — bond-ops

`bond-ops` is a standalone local package: it can be run, tested, and verified
entirely from its own directory.

```bash
# from this package's repo root
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/ops_gate.py inventory
```

It inspects sibling packages under the suite root only read-only (reconcile,
gate, health, provisioning). The suite root is auto-detected as the directory
holding this checkout — in the BOND monorepo that is
`projects/working/bond/`, and a standalone clone finds its sibling checkouts in
its own parent directory; either way `--suite-root` overrides it.
