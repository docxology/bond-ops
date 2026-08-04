"""bond-ops — fleet health, aggregate gates, and provisioning for PROJECT BOND.

bond-ops is the Layer-4 QUARTERMASTER package of the 33-package BOND suite.
It owns the canonical suite roster as data, reconciles it against live
directories, runs per-package quality gates, reports per-repo git health, and
emits (informational) herdr provisioning commands for the fleet.

This package is intentionally standalone: it depends only on the standard
library and subprocess, plus PyYAML for manuscript configuration. It does not
import any sibling BOND package.
"""

from __future__ import annotations

from .inventory import (
    BOND_OPS_CODENAME,
    FILM_COUNT,
    INFRA_COUNT,
    SUITE_NAME,
    SUITE_SIZE,
)

__all__ = [
    "BOND_OPS_CODENAME",
    "SUITE_NAME",
    "FILM_COUNT",
    "INFRA_COUNT",
    "SUITE_SIZE",
]

__version__ = "3.0.0"
