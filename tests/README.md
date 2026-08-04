# tests/

Zero-mock, real-subprocess test suite for bond-ops. Run from the package root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

See `AGENTS.md` (this directory) for the test philosophy and module map.
