"""Auto-numbered formalism cross-reference test.

Enforces the manuscript-semantics checklist: every declared figure / table /
equation / definition / proposition label is referenced somewhere in the
numbered prose, every cross-reference resolves to a declaration, and every
Pandoc citation key resolves in ``references.bib``. Numbers are never written
by hand — labels only.
"""

from __future__ import annotations

import re

from conftest import PROJECT_ROOT

MANUSCRIPT = PROJECT_ROOT / "manuscript"
SECTIONS = sorted(MANUSCRIPT.glob("[0-9]*.md"))

#: Cross-referenceable label kinds (pandoc-crossref + formalism.lua).
KINDS = (
    "fig",
    "tbl",
    "eq",
    "sec",
    "def",
    "prop",
    "thm",
    "lem",
    "cor",
    "rem",
    "ax",
    "claim",
    "ex",
)
#: Kinds that must be referenced once declared. Sections are exempt: an
#: abstract is declared but need not be cited anywhere.
MUST_REFERENCE = KINDS[:3] + KINDS[4:]  # everything except "sec"


def _declared(text: str) -> dict[str, set[str]]:
    labels = {kind: set() for kind in KINDS}
    for kind in KINDS:
        labels[kind].update(re.findall(rf"#(?:{kind}):([A-Za-z0-9_-]+)", text))
    return labels


def _referenced(text: str) -> dict[str, set[str]]:
    labels = {kind: set() for kind in KINDS}
    for kind in KINDS:
        labels[kind].update(re.findall(rf"@(?:{kind}):([A-Za-z0-9_-]+)", text))
    return labels


def _all_declared() -> dict[str, set[str]]:
    merged = {kind: set() for kind in KINDS}
    for md in SECTIONS:
        for kind, found in _declared(md.read_text(encoding="utf-8")).items():
            merged[kind] |= found
    return merged


def test_manuscript_has_numbered_sections():
    assert SECTIONS, "expected numbered manuscript sections"


def test_every_reference_resolves():
    declared = _all_declared()
    for md in SECTIONS:
        refs = _referenced(md.read_text(encoding="utf-8"))
        for kind in KINDS:
            for label in refs[kind]:
                assert label in declared[kind], f"{md.name}: [@{kind}:{label}] not declared"


def test_every_formalism_is_referenced():
    declared = _all_declared()
    referenced = {kind: set() for kind in KINDS}
    for md in SECTIONS:
        for kind, found in _referenced(md.read_text(encoding="utf-8")).items():
            referenced[kind] |= found
    for kind in MUST_REFERENCE:
        dangling = sorted(declared[kind] - referenced[kind])
        assert not dangling, f"declared but never referenced: {[(kind, x) for x in dangling]}"


def test_citations_resolve_in_bib():
    bib = (MANUSCRIPT / "references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"@\w+\{([A-Za-z0-9_./:-]+),", bib))
    assert keys, "references.bib should declare at least one entry"
    for md in SECTIONS:
        text = md.read_text(encoding="utf-8")
        for key in re.findall(r"@([A-Za-z0-9_./-]+)(?![:\w])", text):
            assert key in keys, f"{md.name}: citation [{key}] missing from references.bib"
