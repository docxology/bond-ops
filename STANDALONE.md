# STANDALONE.md — bond-ops

`bond-ops` is a standalone local package: it can be run, tested, and verified
entirely from its own directory.

```bash
cd /Users/4d/Documents/GitHub/template/projects/working/bond/bond-ops
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/ops_gate.py inventory
```

It inspects sibling packages under the suite root only read-only (reconcile,
gate, health, provisioning). There is no remote; never push.
