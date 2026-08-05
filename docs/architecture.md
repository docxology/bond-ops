# architecture.md — bond-ops (QUARTERMASTER)

How this package is put together, module by module, and why the boundaries sit
where they do. Companion documents: `agent_instructions.md` (rules for
changing anything here) and `testing_philosophy.md` (how those changes are
proved).

## The shape in one picture

```
scripts/                 thin argv wrappers, no business logic
  ops_gate.py                        -> bond_ops.cli.main
  z_generate_figures.py              -> bond_ops.figures + a real self-gate
  z_generate_manuscript_variables.py -> bond_ops.manuscript_variables
        |
        v
src/bond_ops/            all business logic (stdlib + subprocess + PyYAML + matplotlib)
  inventory.py   pure data + pure reconcile        <- imports nothing local
  gates.py       subprocess gate runner + manifest <- imports inventory
  health.py      git/fs inspection + probes        <- imports inventory (lazily, in sweep)
  provision.py   herdr recipe rendering + execute  <- imports gates, inventory
  cli.py         the `ops` argparse surface        <- imports gates, health, inventory, provision
  figures.py     deterministic Agg renderers       <- imports gates, health, inventory
  manuscript_variables.py  token hydration         <- imports cli, gates, health, inventory, provision
        |
        v
sibling packages         inspected READ-ONLY (never imported, never executed as libraries)
```

The import graph is a DAG rooted at `inventory.py`. Nothing imports `cli.py`
except `manuscript_variables.py` (for `COMMANDS`) and the thin script wrapper,
so the argparse surface can change shape without disturbing the gate runner.

## Module by module

### `inventory.py` — the roster, as data

The authoritative record of what the suite *is*: a frozen tuple of
`PackageRecord(slug, kind, title, codename, rank, year)` — six infrastructure
packages in Layer order followed by twenty-seven film packages in canon order.
`INFRA_COUNT`, `FILM_COUNT` and `SUITE_SIZE` are computed from that tuple,
never typed in, so the roster cannot disagree with its own arithmetic.

Everything else here is pure: `roster()`, `slugs()`, `package_record()`,
`is_known_slug()`, `package_dir()` (raises on an unknown slug), and
`reconcile(root)`, which partitions the roster against the directories actually
on disk into `present` / `missing` / `unexpected` and exposes a `complete`
predicate. There is no I/O beyond a single directory listing and no subprocess
at all.

`DEFAULT_SUITE_ROOT` is derived from this file's own location
(`parents[3]` = `projects/working/bond/`), so the package finds the fleet
without configuration and without a hardcoded absolute path.

### `gates.py` — the aggregate quality gate

Runs the canonical per-package gate and reduces it to a verdict.

- `run_command(cmd, cwd, timeout, env)` — one real subprocess, combined
  stdout+stderr captured. `env=None` (the default) inherits; passing an env
  lets a nested gate target a sibling's own project environment without
  mutating global state.
- `parse_coverage(output)` — reads the percentage from the pytest-cov `TOTAL`
  table, falling back to the `... not reached. Total coverage: X%` failure line
  that some configurations print *instead of* the table. A malformed `TOTAL`
  cell breaks out to the fallback rather than short-circuiting to `None`, so a
  truncated table cannot mask a reported number.
- `coverage_stats(values)` — `measured` / `mean` / `min` / `max`, all `None`
  when nothing was measured.
- `gate_one(dir, ...)` — pytest, then optionally ruff and mypy, each its own
  subprocess with `cwd` set to the package. An absent directory returns
  `present=False, passed=False`. A timeout or launch failure is caught and
  recorded as a failed result carrying the exception text — never as a pass.
- `run_aggregate_gate(...)` — `gate_one` across the roster, with `only_slugs`
  and `limit` as deterministic filters. `limit=0` gates *nothing*; a negative
  limit raises `ValueError`.
- `AggregateGateReport` — `total` / `present` / `passed_count` /
  `failed_count` / `missing_count` / `all_pass` / `coverage_values` /
  `failed_slugs`, plus `to_dict()` producing the versioned manifest.
- `build_manifest` / `manifest_to_json` / `write_manifest` / `parse_manifest` /
  `format_report` — serialization and the human table.

**The manifest embeds no timestamp.** That is deliberate: for a given suite
state, two runs produce byte-identical JSON, which is what makes the
determinism assertion in the test suite meaningful.

There is one place a clock reading can still enter, and it is worth being
explicit about: the `error` field of a failing package is an 800-character
excerpt of that package's *own* test output, and pytest ends its summary with
`1 failed in 0.10s`. `scrub_wallclock()` replaces elapsed-time readings in that
excerpt with `<elapsed>` before it is stored, so the excerpt keeps the failure
text a human needs and loses only the number that cannot be reproduced. Without
it, "byte-identical across runs" would hold for a *passing* fleet and quietly
fail for a failing one — which is exactly the case a fleet gate exists to
report on. The two-invocation determinism tests drive a failing package on
purpose so this cannot regress.

Note the verdict semantics: `all_pass` requires at least one present package
and zero failures among the present ones. Packages *missing* from disk are
counted in `missing_count` but do not by themselves fail the gate — use
`ops inventory` for "is the fleet complete?" and `ops gate` for "does what is
here pass?".

### `health.py` — per-repo health and drift probes

- `parse_porcelain(status)` — pure reduction of `git status --porcelain` text
  to `(modified, untracked)`; blank lines ignored.
- `git_health(dir)` — is-repo, branch, short SHA, clean flag, modified and
  untracked counts, ahead/behind vs `@{upstream}`. Ahead/behind are `None`
  rather than `0` when no upstream exists, which is the normal state in this
  remote-less tree; conflating the two would report "up to date" for a repo
  with nowhere to be up to date with.
- `required_files(dir)` — presence of README.md / AGENTS.md / TODO.md /
  pyproject.toml.
- `lineage_sweep(dir)` — zero-tolerance content scan for the exemplar lineage
  marker, skipping `.git`, `uv.lock`, `.venv`, caches and `output/`. The marker
  is built by string concatenation so this module never contains the contiguous
  literal and cannot flag itself.
- `probe_layout(dir, slug)` — `has_pyproject`, `pyproject_matches_slug` (via a
  minimal `[project] name` reader, because `tomllib` is 3.11+ and this package
  supports 3.10), `has_tests_dir`, `has_src_dir`.
- `tool_versions()` — real `git` / `uv` / `python` version probe; `None` for
  anything not on `PATH`.
- `HealthReport` / `health()` / `sweep()` — composite per package, in roster
  order.

**`layout_ok` is reported but not folded into `healthy`.** The probes are
diagnostics; changing what `healthy` means would silently move a verdict that
`ops health --json` consumers already read. Widen diagnostics, freeze verdicts.

### `provision.py` — herdr provisioning, read-only by default

`build_roster()` turns the roster into `RosterEntry` records (slug, kind,
codename, absolute cwd, resolved prompt path or `None`); `resolve_prompt()`
looks for `<prompts>/infra/<slug>.{txt,md}` then `<prompts>/<slug>.{txt,md}`.
`render_provision_script()` emits a deterministic bash script — daemon
reachability check, then per package `workspace create --no-focus`, pane-id
extraction, `agent start --kind hermes --timeout …`, and a fire-and-forget
`agent prompt` only when a brief file exists. `roster_report()` is the
machine-readable twin (totals by kind and prompt coverage, then one record per
entry). `execute_script()` is the only function here that *does* anything, and
it is reachable only through `ops roster --execute`.

`herdr` is resolved through `PATH`, which is what lets the tests drive the
execute path with a real (tiny) shell script named `herdr` instead of a mock.

### `cli.py` — the `ops` surface

Four subcommands, each with a human form and a `--json` form emitting a
versioned manifest: `inventory`, `gate`, `health`, `roster`. `COMMANDS` is the
single source of truth for the subcommand list and is asserted against the real
parser in the tests, because it also feeds the `CLI_COMMAND_COUNT` manuscript
token. Exit codes: `0` success, `1` failed gate verdict, `2` usage error
(unknown slug, negative `--limit`, argparse misuse).

The CLI lives in `src/`, not `scripts/`, precisely so it falls inside the
coverage gate; `scripts/ops_gate.py` is a six-line bootstrap.

### `figures.py` — deterministic visualization

Four renderers on the Agg backend — `plot_roster_composition` (frozen roster
constants), `plot_fleet_health` (a real sweep), `plot_gate_coverage` (bars plus
the floor reference line), `plot_gate_verdicts` (pytest/ruff/mypy/passed
heatmap) — plus a `_text_only` placeholder for empty-input cases so a figure
target always exists. Colours are the Wong colourblind-safe palette. Fixed
figure sizes, fixed dpi, no timestamps, no random draws: same inputs, same
bytes.

### `manuscript_variables.py` — token hydration

Identity tokens (`PACKAGE_NAME`, `CODENAME`) come from
`manuscript/config.yaml`; every other token is derived from a live code
constant — roster sizes from `inventory`, coverage floor / gate timeout /
manifest name from `gates`, required-file count from `health`, subcommand count
from `cli`, agent-start timeout from `provision`. Change a constant and the
manuscript moves with it. Measured values (coverage %, test counts) are
deliberately **not** tokens; they are runtime diagnostics recorded in
`docs/_generated/COUNTS.md`.

## What this package deliberately does not have

**There is no `mission.py` here, and no `MissionProvider` implementation.**

The `MissionProvider` protocol is defined in `bond-api`
(`bond_api.protocol.MissionProvider`: a `film` attribute plus `brief`, `recon`,
`plan`, `execute`, `debrief`) and implemented by the twenty-seven *film*
packages, each exposing `mission.MissionProvider` for `bond_api.discovery` to
find. `bond-ops` is Layer-4 fleet operations: the instrument that measures
whether those packages hold up, not one of the things being measured. Making
the gate runner a mission provider would fold the measuring instrument into its
own population — the aggregate gate would gate itself as a peer, and a provider
fault would become indistinguishable from a gate fault.

Concretely, `src/bond_ops/` imports **nothing** from `bond-api` or any other
sibling. Every package in the suite, film or infrastructure, is treated
identically: a directory with tests to run, a git tree to inspect, and a layout
to probe. The same reasoning applies to the `GADGETS` registry consumed by
`bond-cli` — a film-package surface this package neither declares nor reads.

## Rules that hold across all of it

**Dependency rule.** `src/bond_ops/` imports only the standard library,
`subprocess`, PyYAML and (in `figures.py`) matplotlib. No `infrastructure.*`,
no sibling BOND package. When `bond-coordinator` publishes a machine-readable
registry, bind through the integration point recorded in `TODO.md` — reconcile
against it, do not hard-import it.

**One package per subprocess.** `run_aggregate_gate` → `gate_one` launches
`pytest --cov=src --cov-fail-under=90` once per package with `cwd` set to that
package. Scaffold `conftest.py` files mutate `sys.path`; batching packages into
one pytest process collides them. Commands are injectable so tests can drive
deterministic fake packages through the venv interpreter.

**Defaults are read-only.** Inventory, gate, health and roster all inspect.
Only `roster --execute` starts anything, and it shells out through `bash` with
`set -euo pipefail`.

**Real-fleet self-test.** `tests/test_real_fleet.py` gates `bond-ops` itself
through the venv interpreter with real pytest-coverage, ruff and mypy
(`--ignore=tests/test_real_fleet.py` prevents recursion), and runs the health,
layout and toolchain probes against live siblings. The QUARTERMASTER is
verified on the fleet it operates.

## Adding a new fleet check

1. Put the pure logic (a parse function plus a result dataclass) in the
   relevant `src/bond_ops/` module — never in `scripts/`.
2. Surface it through `bond_ops.cli`, adding it to `COMMANDS` if it is a new
   subcommand (the parser-parity test catches a mismatch).
3. Cover it with a real-filesystem / real-subprocess test.
4. If it produces a number the manuscript should quote, add a derived token in
   `manuscript_variables.py` **and** to `manuscript/config.yaml` — the token-set
   test requires the two to agree.
