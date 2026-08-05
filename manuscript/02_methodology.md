# Methodology {#sec:methodology}

## Inventory

`src/bond_ops/inventory.py` carries the canonical roster as data
([@def:suite-roster]) and reconciles it against the live suite root, flagging
missing or unexpected packages ([@def:inventory-reconcile]).

::: {.definition #def:inventory-reconcile title="Reconciliation"}
`inventory.reconcile(root)` partitions the roster into `present` (slug
directory exists under `root`), `missing` (roster slug absent), and
`unexpected` (non-hidden directories on disk that are not roster slugs). The
fleet is *complete* exactly when the missing set is empty
([@eq:reconcile-verdict]).
:::

$$
\operatorname{complete}(r) \iff \operatorname{missing}(r) = \varnothing
$$ {#eq:reconcile-verdict}

## Aggregate gate

::: {.definition #def:aggregate-gate title="Aggregate gate"}
The *aggregate gate* runs the canonical per-package gate — `uv run pytest
tests/ --cov=src --cov-fail-under={{COVERAGE_FLOOR}}` — **once per package in
its own subprocess**, plus ruff and mypy, and aggregates the verdicts into the
machine-readable `{{GATE_MANIFEST}}` manifest.
:::

::: {.proposition #prop:isolation title="One package per subprocess"}
Gating multiple packages in a single pytest process is forbidden: scaffold
`conftest.py` files mutate `sys.path` and collide. Each package's gate
therefore runs with `cwd` set to that package's own directory, one subprocess
per package.
:::

Coverage is parsed from either the pytest-cov `TOTAL` table or the
`... not reached. Total coverage: X%` failure line. The manifest summarises
measured coverage across the fleet with the mean and extrema of the
per-package values ([@eq:coverage-mean], [@eq:coverage-extrema]).

$$
\mu = \frac{1}{n} \sum_{i=1}^{n} c_i
$$ {#eq:coverage-mean}

$$
\min_i c_i \;\le\; c_i \;\le\; \max_i c_i
$$ {#eq:coverage-extrema}

A package's gate verdict is the conjunction of the coverage gate and, when
run, the ruff and mypy checks ([@eq:gate-verdict]):

$$
G(p) = \mathrm{pytest}(p) \;\land\; \mathrm{ruff}(p) \;\land\; \mathrm{mypy}(p)
$$ {#eq:gate-verdict}

The toolchain is standard and pinned via `uv.lock`: [@pytest] drives every
package's tests, [@coveragepy] measures line+branch coverage, [@ruff] lints
and formats, and [@mypy] checks types. [@fig:gate-coverage] and
[@fig:gate-verdicts] visualise a real gate run; [@tbl:toolchain] lists the
tools.

## Health

::: {.definition #def:health-verdict title="Health verdict"}
A package is *healthy* when it is present, ships all required files (README /
AGENTS / TODO / pyproject), is free of lineage hits, and has a clean git tree.
Layout probes additionally flag pyproject-name-vs-slug drift and missing
`tests/` / `src/` directories ([@eq:health-verdict]).
:::

$$
H(p) = \mathrm{present}(p) \land \mathrm{files}(p) \land \neg \mathrm{lineage}(p) \land \mathrm{clean}(p)
$$ {#eq:health-verdict}

## Provisioning

::: {.definition #def:provisioning-roster title="Provisioning roster"}
The *provisioning roster* maps each package to a herdr provisioning recipe —
`workspace create` (capturing the root pane id), `agent start` in that pane,
and a fire-and-forget `agent prompt` when a mission brief file exists.
Rendering is pure and read-only; execution requires an explicit `--execute`.
:::

See [@sec:results] for the measured fleet surface and [@sec:setup] for the
experimental setup.
