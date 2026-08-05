"""Tests for src/bond_ops/manuscript_variables.py — token map + config hydration."""

from __future__ import annotations

import json
import re

from conftest import PROJECT_ROOT

from bond_ops import manuscript_variables as mv


def test_build_tokens_values():
    tokens = mv.build_tokens(PROJECT_ROOT)
    assert tokens["PACKAGE_NAME"] == "bond-ops"
    assert tokens["CODENAME"] == "QUARTERMASTER"
    assert tokens["SUITE_NAME"] == "PROJECT BOND"
    assert tokens["SUITE_SIZE"] == "33"
    assert tokens["FILM_COUNT"] == "27"
    assert tokens["INFRA_COUNT"] == "6"


def test_read_identity_default_when_absent(tmp_path):
    ident = mv.read_identity(tmp_path)
    assert ident["package_name"] == "bond-ops"
    assert ident["codename"] == "QUARTERMASTER"


def test_read_identity_from_config(tmp_path):
    cfg = tmp_path / "manuscript"
    cfg.mkdir()
    (cfg / "config.yaml").write_text("package:\n  name: foo\n  codename: BAR\n", encoding="utf-8")
    ident = mv.read_identity(tmp_path)
    assert ident == {"package_name": "foo", "codename": "BAR"}


def test_read_identity_non_dict(tmp_path):
    cfg = tmp_path / "manuscript"
    cfg.mkdir()
    (cfg / "config.yaml").write_text("- just\n- a list\n", encoding="utf-8")
    assert mv.read_identity(tmp_path)["package_name"] == "bond-ops"  # default fallback


def test_generate_variables_writes(tmp_path):
    tokens = mv.generate_variables(tmp_path)
    assert tokens["CODENAME"] == "QUARTERMASTER"
    path = tmp_path / "output" / "variables" / "manuscript_variables.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["CODENAME"] == "QUARTERMASTER"


def test_load_generated(tmp_path):
    assert mv.load_generated(tmp_path) == {}  # absent -> empty
    mv.generate_variables(tmp_path)
    loaded = mv.load_generated(tmp_path)
    assert loaded["CODENAME"] == "QUARTERMASTER"


def test_all_manuscript_tokens_generated():
    """Every {{TOKEN}} in the numbered prose sections resolves in build_tokens()."""
    tokens = mv.build_tokens(PROJECT_ROOT)
    assert tokens  # non-empty
    numbered = sorted(PROJECT_ROOT.glob("manuscript/[0-9]*.md"))
    assert numbered, "expected numbered manuscript sections"
    for md in numbered:
        text = md.read_text(encoding="utf-8")
        for tok in re.findall(r"\{\{([A-Z_][A-Z0-9_]*)\}\}", text):
            assert tok in tokens, f"{md.name}: unresolved token {{{{tok}}}}"


def test_read_identity_malformed_yaml_falls_back(tmp_path):
    """A malformed config must degrade to the built-in identity, not crash."""
    cfg = tmp_path / "manuscript"
    cfg.mkdir()
    (cfg / "config.yaml").write_text("package: [unclosed\n", encoding="utf-8")
    ident = mv.read_identity(tmp_path)
    assert ident["package_name"] == "bond-ops"
    assert ident["codename"] == "QUARTERMASTER"


def test_load_generated_corrupt_file_reads_as_empty(tmp_path):
    path = tmp_path / "output" / "variables" / "manuscript_variables.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    assert mv.load_generated(tmp_path) == {}


def test_derived_tokens_track_code_constants():
    """Every non-identity token is derived from a live constant, not typed in."""
    from bond_ops import gates, health, provision
    from bond_ops.cli import COMMANDS

    tokens = mv.build_tokens(PROJECT_ROOT)
    assert tokens["COVERAGE_FLOOR"] == str(gates.COVERAGE_FLOOR)
    assert tokens["GATE_MANIFEST"] == gates.GATE_MANIFEST_NAME
    assert tokens["GATE_TIMEOUT_S"] == str(gates.DEFAULT_TIMEOUT)
    assert tokens["CLI_COMMAND_COUNT"] == str(len(COMMANDS))
    assert tokens["REQUIRED_FILE_COUNT"] == str(len(health.REQUIRED_FILES))
    assert tokens["AGENT_START_TIMEOUT_MS"] == str(provision.AGENT_START_TIMEOUT_MS)


def test_config_token_list_matches_generated_map():
    """manuscript/config.yaml's declared token list must match build_tokens()."""
    import yaml

    config = yaml.safe_load(
        (PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    )
    assert sorted(config["tokens"]) == sorted(mv.build_tokens(PROJECT_ROOT))
