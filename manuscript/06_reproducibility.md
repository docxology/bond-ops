# Reproducibility {#sec:reproducibility}

::: {.proposition #prop:manifest-determinism title="Manifest determinism"}
Gate manifests and manuscript variable maps embed no wall-clock timestamp, so
for an unchanged fleet they are byte-identical across runs.
:::

{{PACKAGE_NAME}} is engineered to be deterministic and reproducible:

- **Fixed roster data.** The {{SUITE_SIZE}}-package roster ({{INFRA_COUNT}}
  infra + {{FILM_COUNT}} films) is a frozen, ordered data structure in
  `src/bond_ops/inventory.py`; order never varies across runs or platforms
  ([@def:suite-roster]).
- **No wall-clock in persisted artifacts.** Gate manifests and manuscript
  variable maps embed no timestamps; for an unchanged fleet they are
  byte-identical across runs ([@prop:manifest-determinism]).
- **Real subprocess, real files.** Every gate, git inspection, lineage sweep,
  and provisioning execution reads actual `subprocess` output and actual
  files — there is no mock or simulated state.
- **Determinism tests.** The test suite pins coverage parsing, manifest
  shape, roster order, provisioning script text, and figure bytes; a
  redundant live run of `ops gate --json` on an unchanged suite is asserted
  byte-identical across two invocations.
- **No untracked randomness.** No `random` draws; nothing depends on
  wall-clock ordering.
