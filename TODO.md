# bond-ops TODO

Remaining work only. Completed phases are not archived here — the code, tests
and manuscript are the record of what shipped. Anything listed below is either
unbuilt or unverified; nothing on this list is done.

## Open work

### 1. Consume a shared suite registry from `bond-coordinator`

`src/bond_ops/inventory.py` carries the 33-slug roster as local data, which
means the roster and `bond-coordinator`'s registry can drift apart silently.
When the coordinator exposes a machine-readable registry (JSON / YAML / entry
point), reconcile against it and treat a mismatch as fleet drift rather than
picking a winner.

*Acceptance:* `ops inventory` still reports 33 present against the live fleet;
the coordinator registry is the single source of truth; a deliberately
mismatched registry produces a non-zero verdict in a test.

*Constraint:* bind through data, not a hard import — `src/bond_ops/` must keep
importing nothing from sibling packages.

### 2. `--require-complete` for the aggregate gate

`AggregateGateReport.all_pass` is true when every *present* package passes;
packages missing from disk are counted but do not fail the verdict. That is the
right default (gate what is here), but it means a half-checked-out fleet can
exit `0`. Add an opt-in `--require-complete` that folds `missing_count == 0`
into the exit code.

*Acceptance:* default behaviour byte-identical to today; with the flag, a root
missing any roster slug exits `1` and says which slugs.

*Constraint:* do not change `all_pass` itself — it is a published manifest
field.

### 3. Write the gate manifest from the CLI

`gates.write_manifest()` exists and is tested, but `ops gate --json` only
prints to stdout, so CI-style use needs a shell redirect. Add
`ops gate --out PATH` routing through `write_manifest`.

*Acceptance:* `--out` writes the same bytes `--json` prints, plus a trailing
newline; the parent directory is created; a test round-trips through
`parse_manifest`.

### 4. Verify the claimed Python 3.10 floor

`pyproject.toml` declares `requires-python = ">=3.10"` and `health.py` hand-rolls
a `[project] name` parser specifically to avoid `tomllib` (3.11+). Nothing has
ever executed this package on 3.10 — the local venv is 3.14 and mypy is pinned
to `python_version = "3.12"`. Either run the suite under a real 3.10
interpreter or raise the declared floor to what is actually tested.

*Acceptance:* the gate passes under the lowest interpreter the metadata claims,
or the metadata is corrected to match reality.

### 5. Cross-environment figure determinism

`tests/test_figures.py` asserts byte-identical PNGs across two renders *in the
same process and environment*. Matplotlib version, font availability and
platform can all move the bytes; the current test cannot see that. Either pin
what determinism actually holds across environments, or narrow the claim in
`docs/testing_philosophy.md` and the manuscript to same-environment
determinism.

*Acceptance:* the documented claim and the enforced claim are the same claim.

### 6. Render the manuscript end-to-end

The manuscript declares auto-numbered formalisms, cross-references and figures,
and the cross-reference test proves every label resolves *textually*. No PDF
has been rendered from this package, so the pandoc-crossref + `formalism.lua`
path is unverified here. Render once through the template pipeline and check
that no `??` reference survives.

*Acceptance:* a rendered PDF with zero unresolved references, and the figure
files actually embedded.

## Standing decisions (not work items)

Recorded so they are not "fixed" by a later pass that mistakes them for gaps:

- **No `mission.py`, no `MissionProvider`, no `GADGETS`.** The gate runner must
  not be a member of the population it grades. See `docs/architecture.md`.
- **`layout_ok` is not folded into `healthy`.** Probes are additive
  diagnostics; the verdict is a published contract.
- **Gate manifests carry no timestamp.** That absence is what makes the
  determinism assertion meaningful.
- **Measured numbers are never manuscript tokens.** Coverage and test counts
  are runtime diagnostics recorded in `docs/_generated/COUNTS.md`.

## Quality gates (how to check, not what the numbers are)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
```

Live measured counts: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
