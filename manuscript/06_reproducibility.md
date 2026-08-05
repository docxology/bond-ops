# Reproducibility {#sec:reproducibility}

::: {.proposition #prop:manifest-determinism title="Manifest determinism"}
Gate manifests and manuscript variable maps embed no wall-clock timestamp, so
for an unchanged fleet they are byte-identical across runs. The one place a
clock reading can enter is the free-text `error` excerpt captured from a
failing package's own test output (pytest ends its summary with `1 failed in
0.10s`); elapsed-time readings are redacted from that excerpt before it is
persisted, which is what extends the property from a passing fleet to a
failing one.
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
  shape, roster order, provisioning script text, and figure bytes. The
  cross-run claim is checked by running the gate *twice* — two separate live
  invocations, each spawning its own real test subprocess against the same
  on-disk fleet — and diffing the two payloads, at both the module and the CLI
  surface. The CLI-level check runs against a package whose test output stamps
  a **different** elapsed time on every invocation, so the assertion fails if
  any clock reading survives into the manifest; it is not satisfied by
  serializing one report twice.
- **Recovery paths are tested, not assumed.** The three places where
  {{PACKAGE_NAME}} degrades instead of raising — a malformed
  `manuscript/config.yaml`, a corrupt generated token file, and a gate
  subprocess that times out or cannot be launched — each carry a test that
  drives the real failure and asserts the fallback, so a silent-failure path
  cannot rot unobserved behind a coverage exclusion.
- **Filters cannot silently widen.** `--limit 0` gates nothing and a negative
  limit is a usage error, so a mistyped bound can never expand into a
  full-fleet run.
- **No untracked randomness.** No `random` draws; nothing depends on
  wall-clock ordering.
