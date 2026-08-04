# Scope and Related Work

## Scope

{{PACKAGE_NAME}} covers fleet *operations* only: knowing the {{SUITE_SIZE}}-package roster, gating each package, inspecting health, and rendering provisioning. It does **not** implement the `MissionProvider` protocol (that is `bond-api`), does **not** dispatch multi-package missions (that is `bond-orchestrator`), and does **not** provide the user-facing front door (that is `bond-cli`). Its gate runs each package's *own* tests; it never executes another package's mission logic.

## Related work within the fleet

- **bond-coordinator (MISSION CONTROL)** maintains the film-package registry and mission ledger. {{PACKAGE_NAME}} currently carries the roster as mirror data; an integration point is recorded in `TODO.md` to consume `bond_coordinator.registry.ROSTER` for film metadata once the coordinator ships as a dependency, with the acceptance criterion that the reconciled slug set stays identical to the canonical {{SUITE_SIZE}}.
- **bond-cli (THE FRONT DOOR)** may consume the gate manifest produced here (`bond-ops-gate`, schema v1) to surface fleet status to an end user.
- **bond-api (THE PROTOCOL)** defines the protocol the film packages implement; {{PACKAGE_NAME}} does not depend on it, but a film package fails the aggregate gate if it stops meeting protocol-backed tests.

## External dependencies

The fleet's toolchain (pytest/pytest-cov, ruff, mypy, uv) is standard and versioned via `uv.lock`; the manifest schema and CLI surface are the stable interfaces documented in `docs/`.
