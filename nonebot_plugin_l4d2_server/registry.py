"""Server registry: load, normalize, and look up server groups.

v1.4.0 起 ``_normalize_server_entry`` 保留已有 ``id``（避免 ``云1`` 这类后缀
指令失效），并提供 ``add_server`` / ``remove_server`` / ``update_server``
内存接口，底层走 ``store/groups.py`` 持久化，再回灌内存。

``load_all`` 是所有刷新指令（l4reload / l4reloadsb / l4addban / 单服 CRUD）
共用的内存刷新入口：新表建好后一次性替换，``add_command`` 注册的别名
（如 ``anne``）重载后仍然保留。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path
from typing import Iterable

import aiofiles
from nonebot.log import logger

from .consts import LEGACY_GROUP_SUBDIR, LEGACY_URL_FILENAME, NON_GROUP_FILENAMES
from .http_helpers import split_maohao


def _iter_server_files() -> Iterable[tuple[Path, bool]]:
    """Yield ``(path, is_single_file_multi_group)`` for each loadable JSON.

    Scans: primary flat directory (config.data_dir) → legacy subdirectory
    → legacy URL file. ``is_single_file`` is True only for the legacy
    single-file format where the JSON object has multiple group keys.
    """
    from .config import config

    primary = config.data_dir
    legacy_group = primary / LEGACY_GROUP_SUBDIR
    legacy_url = primary / LEGACY_URL_FILENAME

    roots = [primary]
    if legacy_group.is_dir() and legacy_group.resolve() != primary.resolve():
        roots.append(legacy_group)
    for root in roots:
        # 目录尚未创建（首次启动 / 用户清空）—— 静默跳过，_on_startup 会 mkdir。
        try:
            entries = list(root.iterdir())
        except FileNotFoundError:
            logger.debug(f"数据目录不存在，跳过扫描: {root}")
            continue
        for item in entries:
            if not (item.is_file() and item.suffix == ".json"):
                continue
            if item.stat().st_size == 0:
                logger.debug(f"跳过空文件 {item}")
                continue
            if root is primary and item.name in NON_GROUP_FILENAMES:
                continue
            yield item, False

    if legacy_url.is_file() and legacy_url.stat().st_size > 0:
        yield legacy_url, True


def _source_rank(path: Path, group: str, *, is_single: bool) -> int:
    """同名组出现在多个文件里时的优先级，越小越优先。

    ``<组名>.json`` 是 l4addban / l4reloadsb / 单服 CRUD 的写入目标，必须压过
    多组合并文件、旧版 ``l4d2/`` 子目录、旧版 ``l4d2.json`` 里的同名旧数据，
    否则刷新写盘之后内存里仍是旧列表。
    """
    from .config import config

    if is_single:
        return 3
    if path.parent != config.data_dir:
        return 2
    return 0 if path.stem == group else 1


def _coerce_ip(entry: object) -> str:
    """从任意条目抽 ip 字符串；无法解析返回空串。"""
    if isinstance(entry, str):
        return entry.strip()
    if isinstance(entry, dict):
        ip = entry.get("ip")
        if isinstance(ip, str) and ip.strip():
            return ip.strip()
    host = getattr(entry, "host", None)
    port = getattr(entry, "port", None)
    if host and port:
        return f"{host}:{port}"
    return ""


def _normalize_server_entry(
    entry: object,
    idx: int,
    *,
    max_existing_id: int = 0,
) -> dict | None:
    """把原始条目归一为 ``{id, ip, host, port}``。

    优先保留已有 ``id``；缺失时按 ``max(max_existing_id, idx)`` 续号。
    """
    if isinstance(entry, str):
        ip = entry.strip()
        if not ip:
            return None
        new_id = max(max_existing_id, idx)
        host, port = split_maohao(ip)
        return {"id": str(new_id), "ip": ip, "host": host, "port": port}

    if isinstance(entry, dict):
        one = dict(entry)
        ip = _coerce_ip(entry)
        if not ip:
            logger.warning(f"{one} 没有ip")
            return None
        one["ip"] = ip
        try:
            existing_id = int(one.get("id", 0))
        except (TypeError, ValueError):
            existing_id = 0
        if existing_id <= 0:
            existing_id = max(max_existing_id, idx)
        one["id"] = str(existing_id)
        if not one.get("host") or not one.get("port"):
            host, port = split_maohao(ip)
            one["host"] = one.get("host") or host
            one["port"] = one.get("port") or port
        return one

    logger.warning(f"跳过无法识别的服务器条目: {entry!r}")
    return None


class ServerRegistry:
    """Holds all loaded server groups and command aliases."""

    def __init__(self) -> None:
        self._groups: dict[str, list[dict]] = {}
        self._commands: set[str] = set()
        # add_command 注册的纯别名（如 anne），重建指令表时要带上。
        self._aliases: set[str] = set()
        self._load_lock = asyncio.Lock()

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
        """Replace the entries for ``name`` while preserving existing ids.

        旧版本会把 id 强制重排成 1..N；现在按 ``_normalize_server_entry`` 续号，
        保证 ``云1`` 这类后缀指令的引用稳定。
        """
        max_id = 0
        for e in self._groups.get(name, []):
            with contextlib.suppress(TypeError, ValueError):
                max_id = max(max_id, int(e.get("id", 0)))
        normalised: list[dict] = []
        for idx, raw in enumerate(servers, start=1):
            entry = _normalize_server_entry(
                raw, idx, max_existing_id=max_id,
            )
            if entry is None:
                continue
            try:
                cur_id = int(entry.get("id", 0))
            except (TypeError, ValueError):
                cur_id = 0
            max_id = max(max_id, cur_id)
            normalised.append(entry)
        self._groups[name] = normalised
        self._commands.add(name)

    def add_command(self, name: str) -> None:
        """Register ``name`` as a known command without servers (e.g. anne).

        别名单独记一份，``load_all`` / ``scan_commands`` 重建指令表后仍然有效。
        """
        self._aliases.add(name)
        self._commands.add(name)

    def remove_group(self, name: str) -> bool:
        """Remove ``name`` entirely. Returns True if it was present."""
        if name in self._groups:
            del self._groups[name]
        self._commands.discard(name)
        self._aliases.discard(name)
        return name in self._commands

    def get_server(self, name: str, identifier: str | int) -> dict | None:
        """按 id 或 ip 查组内单服；找不到返回 None。"""
        servers = self._groups.get(name)
        if not servers:
            return None
        if isinstance(identifier, int) or (
            isinstance(identifier, str) and identifier.isdigit()
        ):
            target = str(int(identifier))
            for e in servers:
                if str(e.get("id", "")) == target:
                    return e
            return None
        target_ip = identifier.strip() if isinstance(identifier, str) else ""
        for e in servers:
            if e.get("ip") == target_ip:
                return e
        return None

    async def add_server(self, tag: str, ip: str) -> dict:
        """新增单服：底层走 store/groups.add_server，再 reload_all。"""
        from .store import groups as groups_store

        entry = await groups_store.add_server(tag, ip)
        await self.load_all()
        return entry

    async def remove_server(self, tag: str, identifier: str | int) -> bool:
        """删除单服：底层走 store/groups.remove_server，再 reload_all。"""
        from .store import groups as groups_store

        ok = await groups_store.remove_server(tag, identifier)
        if ok:
            await self.load_all()
        return ok

    async def update_server(
        self,
        tag: str,
        identifier: str | int,
        new_ip: str,
    ) -> dict | None:
        """修改单服：底层走 store/groups.update_server，再 reload_all。"""
        from .store import groups as groups_store

        entry = await groups_store.update_server(tag, identifier, new_ip)
        if entry is not None:
            await self.load_all()
        return entry

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
        found: set[str] = set()
        for path, _is_single in _iter_server_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"读取 {path} 失败: {exc}")
                continue
            if not isinstance(data, dict):
                continue
            found.update(k for k in data if isinstance(k, str))
        self._commands = found | self._aliases
        logger.debug(f"扫描到组名: {self._commands}")

    async def load_all(self) -> None:
        """Reload all groups from disk, normalising every entry.

        新表先建在局部变量里，读完再一次性替换：重载途中进来的查询看到的是
        旧数据而不是被清空的中间态。加锁串行化，避免并发重载互相覆盖。
        """
        async with self._load_lock:
            groups: dict[str, list[dict]] = {}
            ranks: dict[str, int] = {}
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
                    file_groups = {k: v for k, v in raw.items() if isinstance(v, list)}
                else:
                    file_groups = raw

                for group, entries in file_groups.items():
                    rank = _source_rank(path, group, is_single=is_single)
                    if group in ranks:
                        if ranks[group] <= rank:
                            logger.warning(f"组「{group}」在多个文件中重复定义，忽略 {path}")
                            continue
                        logger.warning(f"组「{group}」在多个文件中重复定义，以 {path} 为准")
                    normalised: list[dict] = []
                    if isinstance(entries, list):
                        max_id = 0
                        for idx, raw_entry in enumerate(entries, start=1):
                            norm = _normalize_server_entry(
                                raw_entry, idx, max_existing_id=max_id,
                            )
                            if norm is None:
                                continue
                            try:
                                cur_id = int(norm.get("id", 0))
                            except (TypeError, ValueError):
                                cur_id = 0
                            max_id = max(max_id, cur_id)
                            normalised.append(norm)
                    groups[group] = normalised
                    ranks[group] = rank
                    logger.success(
                        f"成功加载 {path.name.split('.')[0]} {len(normalised)}个",
                    )
            self._groups = groups
            self._commands = set(groups) | self._aliases


# Module-level singleton.
registry = ServerRegistry()
