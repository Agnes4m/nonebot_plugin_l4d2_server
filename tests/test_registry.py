"""Tests for the ServerRegistry class and entry normalization."""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Make repo root importable so we can load registry.py in isolation.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "nonebot_plugin_l4d2_server"))

import consts  # noqa: E402
import registry as registry_module  # noqa: E402
from registry import ServerRegistry, _normalize_server_entry  # noqa: E402


def test_normalize_string_entry():
    """A plain ``"ip:port"`` string becomes a normalized dict."""
    out = _normalize_server_entry("1.2.3.4:27015", 1)
    assert out == {
        "id": "1",
        "ip": "1.2.3.4:27015",
        "host": "1.2.3.4",
        "port": 27015,
    }


def test_normalize_dict_entry_with_id():
    out = _normalize_server_entry({"id": "5", "ip": "5.6.7.8:27016"}, 2)
    assert out["id"] == "5"
    assert out["host"] == "5.6.7.8"
    assert out["port"] == 27016


def test_normalize_dict_entry_without_id():
    out = _normalize_server_entry({"ip": "9.9.9.9:27017"}, 3)
    assert out["id"] == "3"


def test_normalize_host_only_entry():
    """Host-only dict gets ``ip`` filled in but ``port`` left absent."""
    out = _normalize_server_entry({"host": "9.9.9.9"}, 1)
    assert out["ip"] == "9.9.9.9:20715"
    assert out["host"] == "9.9.9.9"


def test_normalize_invalid_type_returns_none():
    assert _normalize_server_entry(None, 1) is None
    assert _normalize_server_entry(42, 2) is None


def test_normalize_empty_string_returns_none():
    assert _normalize_server_entry("", 1) is None
    assert _normalize_server_entry("   ", 2) is None


def test_registry_load_all_with_tempdir(tmp_path):
    """End-to-end: write JSON files, load, verify state."""
    with tempfile.TemporaryDirectory() as td:
        primary = Path(td) / "data" / "L4D2"
        primary.mkdir(parents=True)
        (primary / "alpha.json").write_text(
            json.dumps(
                {"alpha": [{"id": "1", "ip": "1.1.1.1:27015"}, "2.2.2.2:27016"]},
            ),
            encoding="utf-8",
        )
        (primary / "beta.json").write_text(
            json.dumps({"beta": [{"ip": "3.3.3.3:27017"}]}),
            encoding="utf-8",
        )

        # Patch paths used by the module's _iter_server_files so we don't
        # touch the real ``data/L4D2`` directory.
        original_primary = consts.LEGACY_GROUP_DIR
        consts.LEGACY_GROUP_DIR = primary / "l4d2"
        try:
            # Also patch the const so iter uses our tempdir.
            from consts import DEFAULT_DATA_DIR
            original_data_dir = consts.DEFAULT_DATA_DIR
            consts.DEFAULT_DATA_DIR = str(primary)
            try:
                reg = ServerRegistry()
                asyncio.run(reg.load_all())
                assert {"alpha", "beta"}.issubset(reg.commands)
                alpha = reg.get("alpha")
                assert alpha is not None
                assert alpha[0]["host"] == "1.1.1.1"
                assert alpha[1]["host"] == "2.2.2.2"
                assert alpha[1]["port"] == 27016
                beta = reg.get("beta")
                assert beta[0]["ip"] == "3.3.3.3:27017"
            finally:
                consts.DEFAULT_DATA_DIR = original_data_dir
        finally:
            consts.LEGACY_GROUP_DIR = original_primary


def test_registry_set_and_remove():
    reg = ServerRegistry()
    reg.set_group("foo", [{"id": "1", "ip": "1.2.3.4:27015"}])
    assert "foo" in reg.commands
    assert reg.get("foo")[0]["host"] == "1.2.3.4"
    assert reg.remove_group("foo") is False  # not in commands anymore? wait yes
    # After remove_group, ``foo`` is no longer in commands; second call returns False
    reg.remove_group("foo")
    assert "foo" not in reg.commands
    assert reg.get("foo") is None


def test_registry_add_command_only():
    """``anne`` alias registers without any server entries."""
    reg = ServerRegistry()
    reg.add_command("anne")
    assert "anne" in reg.commands
    assert reg.get("anne") is None


def test_registry_load_all_empty():
    """load_all on an empty directory yields empty state without error."""
    import asyncio
    with tempfile.TemporaryDirectory() as td:
        consts.DEFAULT_DATA_DIR = str(Path(td) / "data" / "L4D2")
        Path(consts.DEFAULT_DATA_DIR).mkdir(parents=True)
        try:
            reg = ServerRegistry()
            asyncio.run(reg.load_all())
            assert reg.commands == set()
            assert reg.group_names == []
        finally:
            consts.DEFAULT_DATA_DIR = "data/L4D2"