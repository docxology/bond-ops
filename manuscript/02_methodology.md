# Methodology

## Inventory

`src/bond_ops/inventory.py` carries the **{{SUITE_SIZE}}**-slug roster as data
and reconciles it against live directories, flagging missing or unexpected
packages.

## Aggregate gate

`src/bond_ops/gates.py` runs the canonical per-package gate —
`uv run pytest tests/ --cov=src --cov-fail-under=90` — **once per package in
its own subprocess**, plus ruff and mypy. Results are emitted as a JSON
manifest and a human report.

## Health

`src/bond_ops/health.py` inspects per-repo git state, required-file presence,
and runs a zero-tolerance lineage sweep.

## Provisioning

`src/bond_ops/provision.py` emits the herdr provisioning roster for the fleet,
read-only by default; execution requires an explicit `--execute`.
