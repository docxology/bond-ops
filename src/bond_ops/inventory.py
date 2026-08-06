"""Fleet inventory — the canonical 33-package roster of PROJECT BOND.

bond-ops is the QUARTERMASTER: it owns, as *data*, the authoritative list of
the whole suite — 6 infrastructure packages plus the 27 Eon/non-Eon film
packages — and reconciles that roster against the live directories under the
suite root (``projects/working/bond/``). Nothing here executes other
packages; it only describes them and checks what exists on disk.

The roster is seeded from the fleet conventions recorded in the suite
``ROSTER.md`` / ``SCOPE.md``; the mission codenames are provisional and are
recorded here purely for fleet identity. Coverage/status are *never*
hand-asserted in this module — they come from ``gates.py`` measured gate
output, never from prose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUITE_NAME = "PROJECT BOND"
BOND_OPS_CODENAME = "QUARTERMASTER"

# ---------------------------------------------------------------------------
# Roster records (as data)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackageRecord:
    """One row of the suite roster.

    ``title`` is the film title for a film package and the Layer-role
    description for an infrastructure package. ``rank`` / ``year`` are only
    meaningful for film packages (canon order 1..27); they are ``None`` for
    infrastructure packages.
    """

    slug: str
    kind: str  # "film" | "infra"
    title: str
    codename: str
    rank: int | None = None
    year: int | None = None


#: Infrastructure packages (6) in ascending Layer order.
_INFRA = (
    PackageRecord(
        "bond-utilities",
        "infra",
        "Layer 0 · Q-branch primitives (ciphers, codenames, clocks, seeding, mission IO, fixtures)",
        "Q-BRANCH",
    ),
    PackageRecord(
        "bond-api",
        "infra",
        "Layer 1 · the MissionProvider protocol + registry + discovery + serialization",
        "THE PROTOCOL",
    ),
    PackageRecord(
        "bond-coordinator",
        "infra",
        "Layer 2 · package registry + mission ledger + situation room",
        "MISSION CONTROL",
    ),
    PackageRecord(
        "bond-orchestrator",
        "infra",
        "Layer 3 · multi-package DAG runner, checkpoint/resume",
        "DAG 00",
    ),
    PackageRecord("bond-cli", "infra", "Layer 4 · front door CLI", "THE FRONT DOOR"),
    PackageRecord(
        "bond-ops",
        "infra",
        "Layer 4 · fleet health + aggregate gates + herdr provisioning",
        "QUARTERMASTER",
    ),
)

#: Film packages (27) in Eon canonical order 1..25, then the two non-Eon films.
_FILMS = (
    PackageRecord("dr_no", "film", "Dr. No", "CRAB KEY", rank=1, year=1962),
    PackageRecord(
        "from_russia_with_love", "film", "From Russia with Love", "LURES", rank=2, year=1963
    ),
    PackageRecord("goldfinger", "film", "Goldfinger", "GRAND SLAM", rank=3, year=1964),
    PackageRecord("thunderball", "film", "Thunderball", "DISCO VOLANTE", rank=4, year=1965),
    PackageRecord(
        "you_only_live_twice", "film", "You Only Live Twice", "VOLCANO", rank=5, year=1967
    ),
    PackageRecord(
        "on_her_majestys_secret_service",
        "film",
        "On Her Majesty's Secret Service",
        "PIZ GLORIA",
        rank=6,
        year=1969,
    ),
    PackageRecord(
        "diamonds_are_forever", "film", "Diamonds Are Forever", "CONFLICT STONE", rank=7, year=1971
    ),
    PackageRecord("live_and_let_die", "film", "Live and Let Die", "SAN MONIQUE", rank=8, year=1973),
    PackageRecord(
        "the_man_with_the_golden_gun",
        "film",
        "The Man with the Golden Gun",
        "SOLEX",
        rank=9,
        year=1974,
    ),
    PackageRecord(
        "the_spy_who_loved_me", "film", "The Spy Who Loved Me", "LIPARUS", rank=10, year=1977
    ),
    PackageRecord("moonraker", "film", "Moonraker", "DRAX", rank=11, year=1979),
    PackageRecord("for_your_eyes_only", "film", "For Your Eyes Only", "ATAC", rank=12, year=1981),
    PackageRecord("octopussy", "film", "Octopussy", "FABERGÉ", rank=13, year=1983),
    PackageRecord("a_view_to_a_kill", "film", "A View to a Kill", "ZORIN", rank=14, year=1985),
    PackageRecord(
        "the_living_daylights", "film", "The Living Daylights", "SNIPER'S NEST", rank=15, year=1987
    ),
    PackageRecord("licence_to_kill", "film", "Licence to Kill", "ROGUE", rank=16, year=1989),
    PackageRecord("goldeneye", "film", "GoldenEye", "ARKANGEL", rank=17, year=1995),
    PackageRecord(
        "tomorrow_never_dies", "film", "Tomorrow Never Dies", "CARVER", rank=18, year=1997
    ),
    PackageRecord(
        "the_world_is_not_enough", "film", "The World Is Not Enough", "ELEKTRA", rank=19, year=1999
    ),
    PackageRecord("die_another_day", "film", "Die Another Day", "ICARUS", rank=20, year=2002),
    PackageRecord("casino_royale_2006", "film", "Casino Royale", "LE CHIFFRE", rank=21, year=2006),
    PackageRecord("quantum_of_solace", "film", "Quantum of Solace", "QUANTUM", rank=22, year=2008),
    PackageRecord("skyfall", "film", "Skyfall", "SILVA", rank=23, year=2012),
    PackageRecord("spectre", "film", "Spectre", "NINE EYES", rank=24, year=2015),
    PackageRecord("no_time_to_die", "film", "No Time to Die", "HERACLES", rank=25, year=2021),
    PackageRecord("casino_royale_1967", "film", "Casino Royale", "FIVE 00s", rank=26, year=1967),
    PackageRecord(
        "never_say_never_again", "film", "Never Say Never Again", "REMOUNT", rank=27, year=1983
    ),
)

#: Canonical ordered roster: infra first (Layer order), then films (rank).
ROSTER: tuple[PackageRecord, ...] = _INFRA + _FILMS

INFRA_COUNT = len(_INFRA)  # 6
FILM_COUNT = len(_FILMS)  # 27
SUITE_SIZE = INFRA_COUNT + FILM_COUNT  # 33

#: Default suite root: ``projects/working/bond`` relative to this file.
DEFAULT_SUITE_ROOT = Path(__file__).resolve().parents[3]


def roster() -> tuple[PackageRecord, ...]:
    """Return the canonical 33-package roster (infra first, then films)."""
    return ROSTER


def slugs() -> tuple[str, ...]:
    """Return every slug in canonical order."""
    return tuple(rec.slug for rec in ROSTER)


def package_record(slug: str) -> PackageRecord | None:
    """Return the roster record for ``slug``, or ``None`` if not in the roster."""
    for rec in ROSTER:
        if rec.slug == slug:
            return rec
    return None


def is_known_slug(slug: str) -> bool:
    """Whether ``slug`` names one of the 33 canonical packages."""
    return package_record(slug) is not None


def _dir_entries(suite_root: Path) -> set[str]:
    """Non-hidden directory names directly under ``suite_root``."""
    if not suite_root.is_dir():
        return set()
    return {
        entry.name
        for entry in suite_root.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    }


@dataclass(frozen=True)
class InventoryReport:
    """Result of reconciling the roster against the live suite root."""

    suite_root: str
    present: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]  # non-hidden dirs on disk that are not in the roster

    @property
    def present_count(self) -> int:
        return len(self.present)

    @property
    def missing_count(self) -> int:
        return len(self.missing)

    @property
    def complete(self) -> bool:
        """True when every roster package exists on disk."""
        return self.missing_count == 0


def reconcile(suite_root: str | Path) -> InventoryReport:
    """Reconcile the 33-slug roster against ``suite_root``'s directories.

    Returns an :class:`InventoryReport` describing which roster packages are
    present, which are missing, and which non-hidden directories on disk are
    not part of the roster (informational).
    """
    root = Path(suite_root)
    on_disk = _dir_entries(root)
    known = set(slugs())

    present = [slug for slug in slugs() if slug in on_disk]
    missing = [slug for slug in slugs() if slug not in on_disk]
    unexpected = sorted(on_disk - known)

    return InventoryReport(
        suite_root=str(root),
        present=tuple(present),
        missing=tuple(missing),
        unexpected=tuple(unexpected),
    )


def package_dir(slug: str, suite_root: str | Path = DEFAULT_SUITE_ROOT) -> Path:
    """Absolute path of ``slug`` under the suite root (regardless of existence)."""
    if not is_known_slug(slug):
        raise ValueError(f"unknown suite slug: {slug!r}")
    return Path(suite_root) / slug


def declared_film_codename(package_dir: str | Path, slug: str) -> str | None:
    """Return a present film package's *declared* mission codename, read as data.

    The suite contract gives each film package a ``MissionBrief(codename=...)``
    but the declaration style varies: some inline a literal
    (``codename="SILVA"``), some reference a module constant
    (``codename=CODENAME`` / ``codename=settings.CODENAME`` /
    ``codename=QUANTUM_CODENAME``), and a couple resolve it dynamically
    (``codename=load_scenario().codename``, which reads ``config.yaml``).
    This resolves the value by the cascade below, never by importing a
    sibling — the QUARTERMASTER reads its fleet as data, per the layer
    contract.

    Used by the codename-coherence test to fail loudly when a film package
    renames itself (or this roster row drifts). Returns ``None`` when the
    codename cannot be resolved from disk.
    """
    root = Path(package_dir)
    missions = sorted(root.joinpath("src").rglob("mission.py"))
    if not missions:
        return None
    text = missions[0].read_text(encoding="utf-8", errors="ignore")

    # 1. Inline literal: codename = "X"  (may carry a trailing comma).
    inline = re.search(r'\bcodename\s*=\s*"([^"]+)"', text)
    if inline:
        return inline.group(1)

    # 2. Identifier / dotted reference: codename = IDENT[.CODENAME]
    ref = re.search(
        r"\bcodename\s*=\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*,?\s*$",
        text,
        re.M,
    )
    if ref:
        ident = ref.group(1)
        last = ident.split(".")[-1].lstrip("_")
        # Join with newlines so a constant definition is always at a line start
        # (the ``^`` anchor of the MULTILINE scan) even if the preceding source
        # file does not end with one. Concatenating bare would let one file's
        # trailing code swallow the next file's first definition.
        src_text = (
            "\n".join(
                p.read_text(encoding="utf-8", errors="ignore")
                for p in sorted(root.joinpath("src").rglob("*.py"))
                if p.is_file()
            )
            + "\n"
        )
        double_q = re.compile(rf'^_?{re.escape(last)}\s*=\s*"([^"]*)"', re.M)
        single_q = re.compile(rf"^_?{re.escape(last)}\s*=\s*'([^']*)'", re.M)
        const = double_q.search(src_text) or single_q.search(src_text)
        if const:
            return cast("str", const.group(1))

    # 3. Dynamic ``...().codename`` fallback: the package's own config.yaml.
    config = root.joinpath("manuscript", "config.yaml")
    if config.is_file():
        cfg_text = config.read_text(encoding="utf-8", errors="ignore")
        hits = re.findall(r'codename:\s*"([^"]+)"', cfg_text)
        if hits:
            return cast("str", hits[-1])
    return None
