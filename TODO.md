# TODO — bond-ops (QUARTERMASTER)

`bond-ops` is Layer 4 of PROJECT BOND: it owns the canonical 33-slug fleet roster
as data, runs the per-package quality gate one subprocess at a time, probes every
sibling repository's health, and renders the herdr provisioning roster — while
implementing no mission logic of its own, so the gate runner is never a member of
the population it grades. **Verified state, measured 2026-08-05 in this tree:**
`uv run pytest tests/ --cov=src --cov-fail-under=90` → **133 passed, 0 failed,
0 skipped**, **100.00 %** line+branch coverage over 669 statements / 140 branches
in `src/bond_ops/`, zero `# pragma: no cover` anywhere in `src/`, on Python
3.14.6 / pytest 9.0.2 / pytest-cov 7.0.0 (darwin). The six findings in
`output/verify/bond-ops.json` were all closed by commit `12f3098` and re-checked
against the tree today; none of them is restated below.

Remaining work only. Completed phases are not archived here — the code, tests and
manuscript are the record of what shipped.

---

## Open work

### Correctness — things that are wrong

#### C1. 13 of 27 film codenames disagree with `bond-coordinator`'s registry, and nothing detects it

`src/bond_ops/inventory.py` (`_FILMS`, lines 83–143) and
`bond-coordinator/src/bond_coordinator/registry.py` (the `_record(...)` roster)
both carry a codename per film slug. Slugs, canon ranks, years and titles agree
on all 27 rows; **codenames diverge on 13**. Measured today:

| slug | `bond-ops` | `bond-coordinator` | film package's own declaration |
|---|---|---|---|
| `a_view_to_a_kill` | `ZORIN` | `MAIN STRIKE` | `ZORIN` |
| `casino_royale_1967` | `FIVE 00s` | `FIVE BONDS` | *(none literal)* |
| `diamonds_are_forever` | `CONFLICT STONE` | `DIAMOND NET` | `CONFLICT STONE` |
| `from_russia_with_love` | `LURES` | `LEKTOR` | `LURES` |
| `licence_to_kill` | `ROGUE` | `WAVEKREST` | `ROGUE` |
| `moonraker` | `DRAX` | `MOONRAKER` | `DRAX` |
| `never_say_never_again` | `REMOUNT` | `REPLAY` | `REMOUNT` |
| `octopussy` | `FABERGÉ` | `FABERGE` | `FABERGÉ` |
| `on_her_majestys_secret_service` | `PIZ GLORIA` | `BEDLAM` | `PIZ GLORIA` |
| `skyfall` | `SILVA` | `SKYFALL` | `SILVA` |
| `the_living_daylights` | `SNIPER'S NEST` | `LIVING DAYLIGHTS` | `SNIPER'S NEST` |
| `thunderball` | `DISCO VOLANTE` | `THUNDERBALL` | `DISCO VOLANTE` |
| `you_only_live_twice` | `VOLCANO` | `BIRD ONE` | `VOLCANO` |

The third column is ground truth: each film package declares its own codename via
`bond-api`'s `MissionBrief` (e.g. `skyfall/src/*/mission.py:282` → `SILVA`,
`thunderball/src/*/mission.py:114` → `DISCO VOLANTE`). In every sampled row
`bond-ops` matches the film package and `bond-coordinator` does not, so
`bond-ops` is very probably the correct side — **but nothing here proves that,
and nothing here would notice if a film package renamed itself.** Both registries
document their codenames as "provisional", which is why the divergence has been
invisible.

*Done looks like:* a test in `tests/` that reads each present film package's
declared codename off disk and asserts it equals the `ROSTER` row — failing loudly
on any rename. Not a hard import: read the sibling's declaration as data, per the
layer contract in `AGENTS.md`. Fixing `bond-coordinator` is **out of scope** —
this package never edits siblings.

*Demonstrate with:* `uv run pytest tests/ -k codename -v` (new test), and the
divergence itself is reproducible today with:

```bash
cd .. && python3 - <<'PY'
import sys, re, pathlib
sys.path.insert(0, "bond-ops/src")
from bond_ops.inventory import ROSTER
c = pathlib.Path("bond-coordinator/src/bond_coordinator/registry.py").read_text()
cr = {m[1]: m[4] for m in re.findall(
    r'_record\(\s*(\d+),\s*"([a-z0-9_]+)",\s*"([^"]+)",\s*(\d+),\s*"([^"]+)"', c)}
for r in (x for x in ROSTER if x.kind == "film"):
    if cr.get(r.slug) != r.codename:
        print(r.slug, "| ops", r.codename, "| coordinator", cr.get(r.slug))
PY
```

#### C2. `--pytest-cmd` / `--ruff-cmd` / `--mypy-cmd` cannot accept a real command

`src/bond_ops/cli.py:261-263` declares the three hidden debug overrides with
`nargs="+"`. argparse stops consuming a `nargs="+"` list at the first token that
begins with `-`, so a realistic value is unusable:
`ops gate --pytest-cmd uv run pytest -m pytest --cov=src` parses `-m …` as
unrecognized arguments. The surface is `argparse.SUPPRESS`'d, so no documented
behaviour is wrong — but the option as written cannot do the one job it exists
for, and the CLI determinism test had to route around it with a fake-`uv` `PATH`
override instead. *(Carried from `output/verify/bond-ops.unresolved.json`; flagged
rather than changed because fixing it alters CLI parsing behaviour.)*

*Done looks like:* the three options accept a full command containing leading-dash
tokens (e.g. switch to a single string parsed with `shlex.split`, or `nargs=REMAINDER`),
**and** a test drives `gate` through the option with a command that contains a
`-`-prefixed argument and asserts that command actually ran.

*Demonstrate with:*
`uv run pytest tests/test_cli.py -k pytest_cmd -v` and, by hand,
`uv run python scripts/ops_gate.py gate --only bond-ops --pytest-cmd "uv run pytest tests/ -q"`.

#### C3. The declared Python 3.10 floor has never been executed

`pyproject.toml:19` declares `requires-python = ">=3.10"`, and
`src/bond_ops/health.py:155` hand-rolls a `[project] name` reader specifically to
avoid `tomllib` (3.11+) — a cost paid entirely for a floor nothing has ever run.
Against it: the local interpreter is **3.14.6**, `pyproject.toml:70` pins mypy to
`python_version = "3.12"`, and `docs/architecture.md:120-121` plus
`manuscript/05_experimental_setup.md:3` both restate the ≥3.10 claim in prose.

*Done looks like:* either the full gate passes under a real 3.10 interpreter (and
that fact is recorded in `docs/_generated/COUNTS.md`), or `requires-python`,
`[tool.ruff] target-version`, the two prose sites and the `tomllib` comment are all
lowered/raised to the floor actually exercised.

*Demonstrate with:*
`uv run --python 3.10 pytest tests/ --cov=src --cov-fail-under=90`
(expect: green, or a concrete incompatibility to act on).

#### C4. 63 stray herdr workspaces on the live daemon — needs a human

The pre-existing daemon-guard test created workspaces on Daniel's live herdr
daemon before the leak was fixed (the test now uses the `no_herdr_path` fixture,
`tests/test_provision.py:67`, so nothing new leaks). **Verified still present
today:** 63 workspaces labelled `bond-utilities`, ids `wAS`..`wD6`, `agent_status`
mostly `unknown`. Deleting them is a destructive action on the user's live
environment and outside this package's scope — recorded, not performed.
*(Carried from `output/verify/bond-ops.unresolved.json`.)*

*Done looks like:* Daniel decides; if the decision is "remove", the workspaces are
closed and `herdr workspace list` shows only intentional labels.

*Demonstrate with:*

```bash
herdr workspace list | python3 -c "import sys,json;w=json.load(sys.stdin)['result']['workspaces'];print(sum(1 for x in w if x['label']=='bond-utilities'))"
# currently prints 63; done when it prints 0 (or the surviving count Daniel intends)
```

---

### Verification — claims not yet bound by a test that can fail

#### V1. "Byte-deterministic figures" is asserted only within one process

`tests/test_figures.py:38` (and the three sibling assertions) render twice **in the
same interpreter, same matplotlib, same fonts** and compare bytes. Matplotlib
version, font availability and platform can all move PNG bytes, and this test
cannot see any of that. Meanwhile `docs/testing_philosophy.md:44` and
`manuscript/05_experimental_setup.md:16` state the claim unqualified
("byte-deterministic for fixed inputs").

*Done looks like:* the documented claim and the enforced claim are the same claim —
either the docs and manuscript are narrowed to *same-environment* determinism (with
the environment pinned in `docs/_generated/COUNTS.md`), or a cross-environment
check exists (e.g. compare against a checked-in digest produced under a pinned
matplotlib) that can actually fail when the toolchain moves.

*Demonstrate with:* `uv run pytest tests/test_figures.py -v` plus
`rg -n "byte-deterministic|byte-identical" docs/ manuscript/` showing every site
carries the same scope word.

#### V2. The manuscript has never been rendered end-to-end

`manuscript/` declares auto-numbered formalisms, `@fig:` / `@prop:` cross-references
(`manuscript/03_results.md:24,43,45,47`) and `{{TOKEN}}` substitution.
`tests/test_manuscript_formalisms.py` proves every label resolves **textually**; no
PDF has ever been produced from this package (`find . -name '*.pdf'` → nothing), so
the pandoc-crossref + `formalism.lua` path is unverified here. Note the render
precondition: the manuscript points at `../output/figures/*.png` and `output/` is
gitignored (`.gitignore`, last line), so `scripts/z_generate_figures.py` and
`scripts/z_generate_manuscript_variables.py` must run first or the figures silently
do not embed.

*Done looks like:* a rendered PDF with **zero** unresolved `??` references, all four
figures visibly embedded, and no literal `{{` surviving in the text.

*Demonstrate with:*

```bash
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/z_generate_figures.py
# render through the template pipeline, then:
pdftotext output/pdf/bond-ops.pdf - | rg -n '\?\?|\{\{' || echo clean
```

---

### Documentation

#### D1. README's exit-code list omits the one non-gate failure path

`README.md:81-82` states "Exit codes: `0` success, `1` a failed gate verdict, `2`
usage error". `scripts/AGENTS.md:27-28` documents one more case that is real in the
code: `roster --execute` returns `1` when the provisioning script fails
(`src/bond_ops/cli.py:215`). A reader who trusts only the README would conclude no
command but `gate` can exit non-zero.

*Done looks like:* `README.md` names the `roster --execute` case and states that
`inventory` / `health` / read-only `roster` always exit `0`, matching
`scripts/AGENTS.md` and `manuscript/02_methodology.md:98`.

*Demonstrate with:*
`rg -n "roster --execute" README.md scripts/AGENTS.md` returning both files.

---

### Extension — genuine future work

#### E1. Consume a shared suite registry from `bond-coordinator`

`src/bond_ops/inventory.py` carries the 33-slug roster as local data. As of today
`bond-coordinator` does have a registry module
(`bond-coordinator/src/bond_coordinator/registry.py`, 27 film rows) but exposes no
machine-readable export — no JSON emitter, no entry point. When it does, reconcile
against it and treat a mismatch as *fleet drift* rather than picking a winner.
**Read C1 first:** naively adopting the coordinator's rows today would import 13
stale codenames.

*Done looks like:* `ops inventory` still reports 33 present against the live fleet;
a deliberately mismatched registry produces a non-zero verdict in a test.
*Constraint:* bind through data, not a hard import — `src/bond_ops/` must keep
importing nothing from sibling packages.

*Demonstrate with:* `uv run python scripts/ops_gate.py inventory` and
`uv run pytest tests/test_inventory.py -k registry -v`.

#### E2. `--require-complete` for the aggregate gate

`AggregateGateReport.all_pass` is true when every *present* package passes; packages
missing from disk are counted but do not fail the verdict. That is the right default
(gate what is here), but a half-checked-out fleet exits `0`. Add an opt-in
`--require-complete` that folds `missing_count == 0` into the exit code.

*Done looks like:* default behaviour byte-identical to today; with the flag, a root
missing any roster slug exits `1` and names which slugs. *Constraint:* do not change
`all_pass` itself — it is a published manifest field
(`AGENTS.md`, "Verdicts are frozen").

*Demonstrate with:*
`uv run python scripts/ops_gate.py gate --only dr_no --require-complete; echo $?`
against a root missing a slug (expect `1`), and `uv run pytest tests/test_gates.py -k require_complete -v`.

#### E3. Write the gate manifest from the CLI (`ops gate --out PATH`)

`gates.write_manifest()` exists and is tested, but `_cmd_gate` in
`src/bond_ops/cli.py` only prints to stdout (no `--out` anywhere in the parser), so
CI-style use needs a shell redirect.

*Done looks like:* `--out` writes the same bytes `--json` prints plus a trailing
newline; the parent directory is created; a test round-trips through
`parse_manifest`.

*Demonstrate with:*

```bash
uv run python scripts/ops_gate.py gate --only bond-ops --out output/reports/gate.json
uv run python scripts/ops_gate.py gate --only bond-ops --json | diff - <(head -c -1 output/reports/gate.json)
```

---

## Known limitations (not bugs)

Recorded so a later pass does not mistake them for gaps and "fix" them.

- **The suite must be run as a non-root user.**
  `tests/test_health.py:240-260` reaches the unreadable-file branch with a real
  `chmod 000` file. Root can read such a file, so under root the test **raises
  `AssertionError` rather than skipping** — deliberate, and documented in
  `tests/AGENTS.md:36-38`: a skip would quietly drop a covered line and re-open the
  coverage-pragma question that this package refuses to reopen. The honest scope:
  the suite is **not portable to a root-run environment**. If bond-ops ever gains a
  root CI lane, that branch needs a different real trigger, and this becomes work.
  *(Carried from `output/verify/bond-ops.unresolved.json`.)*
- **No `mission.py`, no `MissionProvider`, no `GADGETS`.** The gate runner must not
  be a member of the population it grades; a provider fault would otherwise be
  indistinguishable from a gate fault. Rationale in `docs/architecture.md` and
  `README.md`.
- **`layout_ok` is not folded into `healthy`.** Probes are additive diagnostics;
  `HealthReport.healthy` is a published contract consumed through the JSON manifest.
- **Gate manifests carry no timestamp.** That absence is what makes the two-run
  byte-identical assertion meaningful
  (`tests/test_gates.py::test_two_live_gate_runs_produce_byte_identical_manifests`).
- **`health` / `inventory` / read-only `roster` always exit `0`.** They are reporting
  commands; the verdict is read from `--json`, not from `$?`. Pinned by
  `tests/test_cli.py::test_health_exit_code_is_zero_even_when_packages_are_unhealthy`.
- **Measured numbers are never manuscript tokens.** Coverage and test counts are
  runtime diagnostics recorded in `docs/_generated/COUNTS.md`, never hand-authored
  into prose.
- **`uv` cannot write `~/.cache/uv` under a restrictive sandbox.**
  `Failed to initialize cache` is an environment restriction, not a package failure.

---

## Verification

The gates for this package, and what each should print:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
#   -> 133 passed; TOTAL 100.00%; "Required test coverage of 90% reached."

uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
#   -> "All checks passed!" and "N files already formatted"

uv run mypy src/ scripts/
#   -> "Success: no issues found"

rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
#   -> clean   (zero-tolerance lineage sweep)

git status --short
#   -> empty after a path-scoped commit
```

Live measured counts and the environment they were measured in:
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md). The floor is the
contract (90 %); the measured value is only a receipt.


---

## Round-2 (2026-08-06)

Committed as `1ce5bb8`. Baseline 133 -> 145 tests.

Round-2 improvement pass: deep code review, verified fixes with regression
tests, manuscript deepened, gates re-run green.

### Baseline (start of round-2)

`uv run pytest tests/ --cov=src --cov-fail-under=90` → **133 passed, 0 failed,
0 skipped**, **100.00 %** line+branch (669 stmts / 140 branches); `ruff check`
clean; `ruff format --check` clean (31 files); `mypy` clean (12 files). Recorded
at the top of this file and in `docs/_generated/COUNTS.md`.

### Findings closed this round

| ID | Finding | Fix (test evidence) |
|---|---|---|
| C2 | `--pytest-cmd` / `--ruff-cmd` / `--mypy-cmd` used `nargs="+"`, so a value with a `-`-prefixed token was unusable. | Options are now single `shlex.split` strings (`cli.py`). `tests/test_cli.py::test_gate_pytest_cmd_accepts_dash_arguments` drives `gate --pytest-cmd "uv run pytest tests/ -q"` and asserts `-q` reached the subprocess. |
| C1 | 13 film codenames historically diverged from `bond-coordinator`'s registry and nothing detected a film renaming itself. | New data-driven resolver `inventory.declared_film_codename()` reads each film package's mission codename as data (literal → module constant → `config.yaml` fallback), never importing a sibling — verified 27/27 against the live fleet. `tests/test_real_fleet.py::test_real_fleet_film_codenames_match_roster` fails loudly on any divergence; 7 positive/negative-control unit tests in `tests/test_inventory.py`. |
| C3 | The declared `>=3.10` floor had never been executed; a hand-rolled `[project] name` parser existed solely to avoid `tomllib` (3.11+), while `mypy` was already pinned to 3.12. | Floor raised to `>=3.12` in `pyproject.toml` (`requires-python`, ruff `target-version = "py312"`), `_read_project_name` rewritten on stdlib `tomllib`, prose updated (`manuscript/05_experimental_setup.md`, `docs/architecture.md`). Malformed-TOML branch covered by `tests/test_health.py::test_probe_layout_malformed_pyproject`. |
| (new) | `bond_ops.__version__` (`"3.0.0"`) disagreed with `[project] version` (`0.1.0`). | Unified on `0.1.0`; bound by new guardrail `tests/test_guardrails.py::test_version_matches_pyproject`. |
| (new) | `declared_film_codename` joined sibling source files with no separator, so the constant `^` anchor failed if a preceding file lacked a trailing newline (invisible live, where files end in newlines; caught by the synthetic apostrophe test). | Join now newline-terminates each file so constant definitions always sit at a line start. `test_declared_film_codename_constant_apostrophe` pins it. |

### Manuscript

- New honest `manuscript/08_limitations_and_uncertainty.md` (gate verdicts are
  necessary-not-sufficient; verdicts narrower than diagnostics; identity is a
  reflection; determinism is same-environment; non-root-portability scope;
  no-wall-clock trade-off; coordinator-registry drift risk).
- `02_methodology.md` / `03_results.md` now describe the codename-coherence
  check and the full-command gate overrides.
- Outputs regenerated (`output/variables/manuscript_variables.json`, four
  figures under `output/figures/`) from the live engine/scripts.
- All numbers stay token-injected; no hand-authored constants added.

### Final gate numbers (this round)

`uv run pytest tests/ --cov=src --cov-fail-under=90` → **145 passed, 0 failed,
0 skipped**, **100.00 %** line+branch over 696 stmts / 146 branches
(Python 3.14.6). `ruff check` clean; `ruff format --check` clean (31 files);
`mypy src/ scripts/` clean (12 files). `rg template[_]code_project` clean.

### Left for a future round

- `C4` — 63 stray herdr workspaces on the live daemon (needs a human decision).
- `E2` — opt-in `--require-complete` for `ops gate`.
- `E3` — `ops gate --out PATH` manifest writer.
- `V2` — end-to-end manuscript PDF render (pandoc pipeline) with no `??`/`{{`.

