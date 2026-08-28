"""Tests for the legacy layout migration."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "nonebot_plugin_l4d2_server"))

import consts  # noqa: E402
import services.migrate as migrate_mod  # noqa: E402


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def test_split_server_data_into_per_tag(tmp_path):
    primary = tmp_path / "data" / "L4D2"
    primary.mkdir(parents=True)
    (primary / "l4d2.json").write_text(
        json.dumps(
            {
                "呆子": [
                    {"id": "1", "ip": "1.2.3.4:27015"},
                    {"id": "2", "ip": "1.2.3.4:27016"},
                ],
                "新呆子": ["5.6.7.8:27015", "5.6.7.8:27016"],
            },
        ),
        encoding="utf-8",
    )

    with _patch(consts, "DEFAULT_DATA_DIR", str(primary)), _patch(
        consts, "LEGACY_URL_FILE", primary / "l4d2.json"
    ):
        migrate_mod.migrate_legacy_layout()

    assert (primary / "呆子.json").is_file()
    assert (primary / "新呆子.json").is_file()
    assert not (primary / "l4d2.json").is_file()
    assert (primary / "l4d2.json.bak").is_file()


def test_url_map_merged_into_pages(tmp_path):
    primary = tmp_path / "data" / "L4D2"
    primary.mkdir(parents=True)
    (primary / "l4d2.json").write_text(
        json.dumps(
            {"cloud": "https://example.com/sb", "other": "https://x.test/"},
        ),
        encoding="utf-8",
    )

    import store.pages as pages_store
    expected_pages_path = primary / "sb_pages.json"

    with _patch(consts, "DEFAULT_DATA_DIR", str(primary)), _patch(
        consts, "LEGACY_URL_FILE", primary / "l4d2.json"
    ), _patch(pages_store, "PAGES_FILE", expected_pages_path):
        migrate_mod.migrate_legacy_layout()

    assert expected_pages_path.is_file()
    assert not (primary / "l4d2.json").is_file()
    pages = json.loads(expected_pages_path.read_text("utf-8"))
    assert pages == {"cloud": "https://example.com/sb", "other": "https://x.test/"}


def test_legacy_subdir_migrated_up(tmp_path):
    primary = tmp_path / "data" / "L4D2"
    legacy = primary / "l4d2"
    legacy.mkdir(parents=True)
    (legacy / "group.json").write_text(
        json.dumps({"group": [{"id": "1", "ip": "1.1.1.1:27015"}]}),
        encoding="utf-8",
    )

    with _patch(consts, "DEFAULT_DATA_DIR", str(primary)), _patch(
        consts, "LEGACY_GROUP_DIR", legacy
    ):
        migrate_mod.migrate_legacy_layout()

    assert (primary / "group.json").is_file()
    assert not legacy.exists()


def test_idempotent(tmp_path):
    primary = tmp_path / "data" / "L4D2"
    primary.mkdir(parents=True)
    (primary / "l4d2.json").write_text(
        json.dumps({"a": [{"ip": "1.1.1.1:27015"}]}),
        encoding="utf-8",
    )
    ctx = [
        _patch(consts, "DEFAULT_DATA_DIR", str(primary)),
        _patch(consts, "LEGACY_URL_FILE", primary / "l4d2.json"),
    ]
    with ctx[0], ctx[1]:
        migrate_mod.migrate_legacy_layout()
    # Second call should be a no-op (file already gone).
    with ctx[0], ctx[1]:
        migrate_mod.migrate_legacy_layout()
    assert (primary / "a.json").is_file()
    assert not (primary / "l4d2.json").exists()


class _patch:
    """Tiny context manager: temporarily override a module attribute."""

    def __init__(self, module, attr: str, value) -> None:
        self.module = module
        self.attr = attr
        self.value = value
        self.original = getattr(module, attr)

    def __enter__(self):
        setattr(self.module, self.attr, self.value)

    def __exit__(self, *exc):
        setattr(self.module, self.attr, self.original)