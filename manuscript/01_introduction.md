# Introduction {#sec:introduction}

The PROJECT BOND suite (**{{SUITE_NAME}}**) comprises **{{SUITE_SIZE}}**
packages: **{{INFRA_COUNT}}** infrastructure packages forming the operational
core (protocol, coordinator, orchestrator, CLI, ops, utilities) and
**{{FILM_COUNT}}** film packages implementing their respective mission
providers. [@fig:roster-composition] shows the composition.

::: {.definition #def:suite-roster title="Suite roster"}
The *suite roster* is the frozen, ordered set of the **{{SUITE_SIZE}}** package
slugs — **{{INFRA_COUNT}}** infrastructure and **{{FILM_COUNT}}** films —
carried as data in `src/bond_ops/inventory.py` and reconciled against live
directories by `inventory.reconcile`.
:::

![Roster composition of {{SUITE_NAME}}: {{INFRA_COUNT}} infrastructure packages and {{FILM_COUNT}} film packages, totalling {{SUITE_SIZE}} packages.](../output/figures/roster_composition.png){#fig:roster-composition width=70%}

The QUARTERMASTER's premise: a fleet this large can only be trusted if it is
inventoried, gated, and provisioned from a single, deterministic vantage
point. `bond-ops` fills exactly that Layer-4 role; the machinery is defined in
[@sec:methodology].
