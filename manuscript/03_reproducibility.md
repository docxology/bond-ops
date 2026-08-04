# Reproducibility

The suite is a local-only working tree (`projects/working/bond/`) with no
remote. Deterministic behaviour is enforced across **{{PACKAGE_NAME}}**'s own
test suite: real subprocesses against real tmp-path fake packages, real `git`
repos, zero mocks, and no wall-clock in committed artifacts. Timestamps appear
only in runtime gate manifests.

Coverage is gated at ≥90% on `src/`; live counts are measured in
`docs/_generated/COUNTS.md` rather than hardcoded in prose.
