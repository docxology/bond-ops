# Scope and Related Work {#sec:scope}

## Scope

{{PACKAGE_NAME}} covers fleet *operations* only: knowing the
{{SUITE_SIZE}}-package roster ([@def:suite-roster]), gating each package
([@def:aggregate-gate]), inspecting health ([@def:health-verdict]), and
rendering provisioning ([@def:provisioning-roster]). It does **not** dispatch
multi-package missions (that is `bond-orchestrator`) and does **not** provide
the user-facing front door (that is `bond-cli`). Its gate runs each package's
*own* tests; it never executes another package's mission logic.

Crucially, {{PACKAGE_NAME}} ships **no `mission.py` and no `MissionProvider`
implementation**, and this is a design decision rather than an omission. The
`MissionProvider` protocol is *defined* by `bond-api` and *implemented* by the
{{FILM_COUNT}} film packages, each of which answers `brief` / `recon` / `plan`
/ `execute` / `debrief` for its own film. A mission provider is a thing the
fleet *runs*; the QUARTERMASTER is the thing that *measures whether the fleet
can be run at all*. Making the gate runner itself a mission provider would put
the measuring instrument inside the population it measures — the aggregate
gate would then have to gate itself as a peer, and a provider failure would be
indistinguishable from a gate failure. `bond-ops` therefore imports nothing
from `bond-api` and treats every package, film or infrastructure, purely as a
directory with tests, a git tree, and a layout to probe.

## Related work within the fleet

- **bond-coordinator (MISSION CONTROL)** maintains the film-package registry
  and mission ledger. {{PACKAGE_NAME}} currently carries the roster as mirror
  data; an integration point is recorded in `TODO.md` to consume
  `bond_coordinator.registry.ROSTER` for film metadata once the coordinator
  ships as a dependency, with the acceptance criterion that the reconciled
  slug set stays identical to the canonical {{SUITE_SIZE}}.
- **bond-cli (THE FRONT DOOR)** may consume the gate manifest produced here
  ([@tbl:gate-manifest]) to surface fleet status to an end user.
- **bond-api (THE PROTOCOL)** defines the protocol the film packages
  implement; {{PACKAGE_NAME}} does not depend on it, but a film package fails
  the aggregate gate if it stops meeting protocol-backed tests.

## External dependencies

The fleet's toolchain ([@tbl:toolchain]) is standard and versioned via
`uv.lock`; the manifest schema ([@tbl:gate-manifest]) and CLI surface are the
stable interfaces documented in `docs/`.
