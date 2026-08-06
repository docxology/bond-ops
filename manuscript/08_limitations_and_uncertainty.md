# Limitations and Uncertainty {#sec:limitations}

## Scope of a gate verdict

A {{COVERAGE_FLOOR}}% line+branch floor is a *necessary*, not a *sufficient*,
condition for correctness. A package whose own suite passes can still be wrong
where its tests do not look: the QUARTERMASTER reports that each package held
its own gate, not that the gate is a proof. This is why measured counts live in
`docs/_generated/COUNTS.md` as receipts rather than being folded into manuscript
prose ([@sec:reproducibility]).

## Verdicts are narrower than their diagnostics

`HealthReport.healthy` ([@def:health-verdict]) deliberately excludes the layout
probes ([@prop:probe-additivity]): a package with a clean tree and all
{{REQUIRED_FILE_COUNT}} required files is `healthy` even if its `[project] name`
has drifted from its slug, because folding the probe in would change the
verdict contract downstream consumers read. The drift is surfaced as
`layout_ok=False`, but that is a diagnostic, not a verdict — a reader who wants
"identity is correct" must inspect `layout_ok`, not `healthy`.

## Fleet identity is a reflection, not a ground truth

The roster ([@def:suite-roster]) and each film's mission codename are
cross-checked as data against every present film package's own declaration.
That declaration is read from source and config files and can itself be stale:
the coherence test catches a film that renamed itself without updating this
roster, but cannot catch a film whose *own* source declares an outdated
codename. The check is only as fresh as the packages it reads.

## Determinism has a same-environment scope

Gate manifests are byte-identical for an unchanged fleet ([@prop:manifest-determinism]), but figure bytes are deterministic *within a pinned environment*:
changing the matplotlib/font stack can move PNG bytes even for identical inputs.
The figure guarantee is therefore reproduced under a fixed toolchain rather than
claimed unconditionally across every platform.

## The suite is not portable to a root-run environment

One health probe reaches its unreadable-file branch with a real `chmod 000`
file; a root user can read such a file, so under root that branch would go
unexercised and the test fails loudly instead of silently dropping coverage
(see `tests/test_health.py`). This is honest scoping, recorded so a later pass
does not mistake it for a gap: the suite is operated as a non-root user.

## No wall-clock, by design

Persisted artifacts carry no timestamp, which is what makes byte-identical
re-runs meaningful, at the cost that a reader cannot tell *when* a manifest was
produced from the artifact alone. Toolchain versioning comes from the `uv.lock`
pin, not from a clock in the file.

## Remaining drift risk: the coordinator registry

{{PACKAGE_NAME}} carries the roster as its own data rather than consuming a
shared registry. When `bond-coordinator` publishes a machine-readable export, a
mismatch must be treated as *fleet drift*, not resolved by picking a winner.
That integration point, and the current codename divergence from the
coordinator's provisional registry, are tracked in `TODO.md`.
