# scripts/

Thin CLI wrappers for bond-ops. Run from the package root:

```bash
uv run python scripts/ops_gate.py inventory
uv run python scripts/ops_gate.py gate --json
uv run python scripts/ops_gate.py health
uv run python scripts/ops_gate.py roster
uv run python scripts/z_generate_manuscript_variables.py
```

See `AGENTS.md` (this directory) for the thin-orchestrator contract.
