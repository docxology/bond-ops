"""Tests for src/bond_ops/inventory.py — roster data + reconciliation."""

from __future__ import annotations

import json

from bond_ops import inventory as inv


def test_roster_counts():
    assert inv.SUITE_SIZE == 33
    assert inv.FILM_COUNT == 27
    assert inv.INFRA_COUNT == 6
    slugs = inv.slugs()
    assert len(slugs) == 33
    assert len(set(slugs)) == 33  # no duplicates
    films = [r for r in inv.ROSTER if r.kind == "film"]
    infra = [r for r in inv.ROSTER if r.kind == "infra"]
    assert len(films) == 27 and len(infra) == 6
    assert [r.slug for r in infra] == [
        "bond-utilities",
        "bond-api",
        "bond-coordinator",
        "bond-orchestrator",
        "bond-cli",
        "bond-ops",
    ]
    assert all(r.rank is not None and r.year is not None for r in films)
    assert [r.rank for r in films] == list(range(1, 28))
    # infra kinds declare no rank/year
    assert all(r.rank is None and r.year is None for r in infra)


def test_package_record_and_known_slug():
    rec = inv.package_record("goldfinger")
    assert rec is not None
    assert rec.codename == "GRAND SLAM"
    assert rec.kind == "film"
    assert inv.package_record("nope") is None
    assert inv.is_known_slug("dr_no") is True
    assert inv.is_known_slug("nope") is False


def test_reconcile_complete(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    for slug in inv.slugs():
        (root / slug).mkdir()
    report = inv.reconcile(root)
    assert report.complete is True
    assert report.present_count == 33
    assert report.missing_count == 0
    assert len(report.present) == 33
    assert report.missing == ()
    assert report.unexpected == ()


def test_reconcile_missing_and_unexpected(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    (root / "goldfinger").mkdir()
    (root / "skyfall").mkdir()
    (root / "extra_dir").mkdir()
    (root / ".hidden").mkdir()
    report = inv.reconcile(root)
    assert report.complete is False
    assert report.present_count == 2
    assert "goldfinger" in report.present and "skyfall" in report.present
    assert report.missing_count == 31
    assert "dr_no" in report.missing
    assert report.unexpected == ("extra_dir",)  # hidden dirs are excluded


def test_reconcile_non_dir(tmp_path):
    report = inv.reconcile(tmp_path / "does_not_exist")
    assert report.present == ()
    assert report.missing_count == 33
    assert report.complete is False


def test_package_dir(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    assert inv.package_dir("goldfinger", root) == root / "goldfinger"
    try:
        inv.package_dir("nope", root)
        raise AssertionError("expected ValueError for unknown slug")
    except ValueError:
        pass


def test_inventory_dict_serializable(tmp_path):
    root = tmp_path / "fleet"
    root.mkdir()
    (root / "goldfinger").mkdir()
    report = inv.reconcile(root)
    payload = {
        "present": list(report.present),
        "missing": list(report.missing),
        "unexpected": list(report.unexpected),
        "complete": report.complete,
    }
    json.dumps(payload)  # must not raise


def test_live_suite_root_complete():
    # Reconcile the real suite root (this package lives inside it): the full
    # 33-package fleet is present in this workspace.
    report = inv.reconcile(inv.DEFAULT_SUITE_ROOT)
    assert report.complete is True
    assert report.present_count == 33


def test_roster_accessor_matches_constants():
    records = inv.roster()
    assert records is inv.ROSTER
    assert len(records) == inv.SUITE_SIZE
    assert sum(1 for r in records if r.kind == "infra") == inv.INFRA_COUNT
    assert sum(1 for r in records if r.kind == "film") == inv.FILM_COUNT
