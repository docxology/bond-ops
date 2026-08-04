# Results

The fleet surface produced by {{PACKAGE_NAME}} (codename {{CODENAME}}), all measured from real subprocess and filesystem state:

- **Inventory.** `ops inventory` reconciles the canonical {{SUITE_SIZE}}-package roster ({{INFRA_COUNT}} infra + {{FILM_COUNT}} films) against `projects/working/bond/` and reports present, missing, and unexpected directories. A complete fleet shows `present {{SUITE_SIZE}}/{{SUITE_SIZE}} · complete yes`.
- **Aggregate gate.** `ops gate --json` emits a deterministic manifest containing, for each package, its presence, pytest pass/fail, measured coverage, ruff and mypy verdicts, and the summary totals (present, passed, failed, missing, coverage min/mean/max). `ops gate` (human form) prints a per-package table; the exit code is `0` iff every present package passes.
- **Fleet health.** `ops health` reports per-repo clean/dirty, branch, ahead/behind, required-file coverage, lineage hits, and an overall healthy/bad verdict.
- **Provisioning roster.** `ops roster` prints the herdr provisioning script; `ops roster --execute` runs it against the herdr daemon.

Because the manifest carries no wall-clock timestamp and asks only real processes for their verdicts, re-running `ops gate` against an unchanged fleet yields an identical manifest — a live determinism check.
