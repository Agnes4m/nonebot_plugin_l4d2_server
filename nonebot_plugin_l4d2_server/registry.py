"""Server registry: single source of truth for loaded server groups.

Replaces the legacy module-level ``ALLHOST`` dict and ``COMMAND`` set in
``server/query/typing.py``. Centralizes loading, normalization, and access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import aiofiles
from nonebot.log import logger

from nonebot_plugin_l4d2_server.consts import LEGACY_GROUP_DIR, LEGACY_URL_FILE
from nonebot_plugin_l4d2_server.http_helpers import split_maohao

# Old layout used these filenames as standalone single-file multi-group
# containers. They are explicitly excluded from per-file scanning.
# sb_pages.json 是“组名→SourceBans URL”映射存储，不是服务器组数据。
_EXCLUDED_TOP_LEVEL_FILES = frozenset({LEGACY_URL_FILE.name, "sb_pages.json"})


def _iter_server_files() -> Iterable[tuple[Path, bool]]:
    """Yield ``(path, is_single_file_multi_group)`` for each loadable JSON.

    Scans: primary flat directory → legacy subdirectory → legacy URL file.
    ``is_single_file`` is True only for the legacy single-file format where
    the JSON object has multiple group keys; otherwise each file holds one
    group's servers.
    """
    from nonebot_plugin_l4d2_server.consts import DEFAULT_DATA_DIR

    primary = Path(DEFAULT_DATA_DIR)
    if primary.is_dir():
        for item in primary.iterdir():
            if (
                item.is_file()
                and item.suffix == ".json"
                and item.name not in _EXCLUDED_TOP_LEVEL_FILES
            ):
                yield item, False

    if LEGACY_GROUP_DIR.is_dir() and LEGACY_GROUP_DIR.resolve() != primary.resolve():
        for item in LEGACY_GROUP_DIR.iterdir():
            if item.is_file() and item.suffix == ".json":
                yield item, False

    if LEGACY_URL_FILE.is_file():
        yield LEGACY_URL_FILE, True


def _normalize_server_entry(
    entry: object,
    idx: int,
) -> dict | None:
    """Coerce a raw JSON entry to ``{id, ip, host, port}`` or skip it."""
    if isinstance(entry, str):
        ip = entry.strip()
        if not ip:
            return None
        one = {"id": str(idx), "ip": ip}
    elif isinstance(entry, dict):
        one = dict(entry)
        one.setdefault("id", str(idx))
    else:
        logger.warning(f"跳过无法识别的服务器条目: {entry!r}")
        return None

    if one.get("ip"):
        if one.get("host") and not one.get("port"):
            one["port"] = 20715
        if not one.get("host"):
            host, port = split_maohao(one["ip"])
            one["host"], one["port"] = host, port
    else:
        if one.get("host") and one.get("port"):
            one["ip"] = f"{one['host']}:{one['port']}"
        elif one.get("host") and not one.get("port"):
            one["ip"] = f"{one['host']}:20715"
        else:
            logger.warning(f"{one} 没有ip")
    return one


class ServerRegistry:
    """Holds all loaded server groups and command aliases."""

    def __init__(self) -> None:
        self._groups: dict[str, list[dict]] = {}
        self._commands: set[str] = set()

    @property
    def commands(self) -> set[str]:
        return set(self._commands)

    @property
    def group_names(self) -> list[str]:
        return list(self._groups.keys())

    def get(self, name: str) -> list[dict] | None:
        """Return servers for ``name``, or ``None`` if not registered."""
        return self._groups.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._commands

    def __iter__(self):
        return iter(self._groups)

    def set_group(self, name: str, servers: list[dict]) -> None:
        """Replace the entries for ``name`` (each entry is normalised in place)."""
        normalised: list[dict] = []
        for idx, raw in enumerate(servers, start=1):
            entry = _normalize_server_entry(raw, idx)
            if entry is not None:
                normalised.append(entry)
        self._groups[name] = normalised
        self._commands.add(name)

    def add_command(self, name: str) -> None:
        """Register ``name`` as a known command without servers (e.g. anne)."""
        self._commands.add(name)

    def remove_group(self, name: str) -> bool:
        """Remove ``name`` entirely. Returns True if it was present."""
        if name in self._groups:
            del self._groups[name]
        self._commands.discard(name)
        return name in self._commands

    def all_json_filenames(self) -> list[str]:
        """Filenames (without .json) of all per-group files (excludes legacy)."""
        names: list[str] = []
        seen: set[str] = set()
        for path, is_single in _iter_server_files():
            if is_single:
                continue
            stem = path.stem
            if stem in seen:
                continue
            seen.add(stem)
            names.append(stem)
        return names

    def scan_commands(self) -> None:
        """Populate ``_commands`` from filenames only, no server data loaded."""
        self._commands.clear()
        for path, _is_single in _iter_server_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"读取 {path} 失败: {exc}")
                continue
            if not isinstance(data, dict):
                continue
            self._commands.update(k for k in data if isinstance(k, str))
        logger.debug(f"扫描到组名: {self._commands}")

    async def load_all(self) -> None:
        """Reload all groups from disk, normalising every entry."""
        self._groups.clear()
        self._commands.clear()
        for path, is_single in _iter_server_files():
            try:
                async with aiofiles.open(path, "r", encoding="utf-8") as f:
                    raw_text = await f.read()
                raw = json.loads(raw_text)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"读取 {path} 失败: {exc}")
                continue
            if not isinstance(raw, dict):
                logger.warning(f"{path} 顶层不是字典, 跳过")
                continue

            if is_single:
                groups = {k: v for k, v in raw.items() if isinstance(v, list)}
            else:
                groups = raw

            for group, entries in groups.items():
                normalised: list[dict] = []
                if isinstance(entries, list):
                    for idx, raw_entry in enumerate(entries, start=1):
                        norm = _normalize_server_entry(raw_entry, idx)
                        if norm is not None:
                            normalised.append(norm)
                self._groups[group] = normalised
                self._commands.add(group)
                logger.success(
                    f"成功加载 {path.name.split('.')[0]} {len(normalised)}个",
                )


# Module-level singleton.
registry = ServerRegistry()
