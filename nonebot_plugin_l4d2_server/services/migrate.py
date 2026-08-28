"""Legacy layout migration (runs once at startup).

Handles three old shapes:
1. ``data/L4D2/l4d2/<tag>.json`` → moved up to ``data/L4D2/<tag>.json``
2. ``data/L4D2/l4d2.json`` with server data (list values) → split into per-tag files
3. ``data/L4D2/l4d2.json`` with URL map (string values) → merged into ``sb_pages.json``

URL maps and server data are distinguished by inspecting the value types.
"""

from __future__ import annotations

import json
from pathlib import Path

from nonebot.log import logger

import consts


def _looks_like_url_map(payload: object) -> bool:
    """True when every value is a non-empty string (a URL)."""
    if not isinstance(payload, dict) or not payload:
        return False
    return all(isinstance(v, str) and v.strip() for v in payload.values())


def _looks_like_servers(payload: object) -> bool:
    """True when any value is a list or dict (server data)."""
    if not isinstance(payload, dict) or not payload:
        return False
    return any(isinstance(v, (list, dict)) for v in payload.values())


def _primary_dir() -> Path:
    return Path(consts.DEFAULT_DATA_DIR)


def migrate_legacy_layout() -> None:
    """Idempotently migrate legacy storage layouts. Safe to call repeatedly."""
    _migrate_legacy_url_file()
    _migrate_legacy_group_dir()


def _migrate_legacy_url_file() -> None:
    if not consts.LEGACY_URL_FILE.is_file():
        return

    try:
        payload = json.loads(consts.LEGACY_URL_FILE.read_text("utf-8") or "{}")
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(f"旧版 {consts.LEGACY_URL_FILE.name} 解析失败: {exc}")
        return

    if _looks_like_url_map(payload):
        _merge_url_map_into_pages(payload)
        _rename_to_backup(consts.LEGACY_URL_FILE)
        return

    if _looks_like_servers(payload):
        assert isinstance(payload, dict)
        _split_servers_into_per_tag_files(payload)
        _rename_to_backup(consts.LEGACY_URL_FILE)


def _merge_url_map_into_pages(entries: dict) -> None:
    """Merge ``{tag: url}`` entries into ``sb_pages.json``."""
    import aiofiles
    from store.pages import PAGES_FILE, load_pages, save_pages

    async def go() -> None:
        pages = await load_pages()
        for tag, url in entries.items():
            tag = str(tag).strip()
            if tag and url and url.strip():
                pages[tag] = url.strip()
        await save_pages(pages)

    import asyncio
    asyncio.run(go())
    logger.success(f"已将 {len(entries)} 个 URL 映射合并到 sb_pages.json")


def _split_servers_into_per_tag_files(entries: dict) -> None:
    """Split ``{tag: [servers]}`` into one file per tag."""
    primary = _primary_dir()
    migrated = 0
    for tag, servers in entries.items():
        if not isinstance(tag, str) or not isinstance(servers, list):
            continue
        target = primary / f"{tag}.json"
        if target.exists():
            continue
        items: list[dict] = []
        for idx, srv in enumerate(servers, start=1):
            if isinstance(srv, str) and srv.strip():
                items.append({"id": str(idx), "ip": srv.strip()})
            elif isinstance(srv, dict) and isinstance(srv.get("ip"), str):
                items.append({"id": str(idx), "ip": srv["ip"].strip()})
        if not items:
            continue
        target.write_text(
            json.dumps({tag: items}, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        migrated += 1
    if migrated:
        logger.success(f"已从旧版 l4d2.json 迁移 {migrated} 个服务器组")


def _migrate_legacy_group_dir() -> None:
    if not consts.LEGACY_GROUP_DIR.is_dir():
        return
    primary = _primary_dir()
    moved = 0
    for old_file in consts.LEGACY_GROUP_DIR.glob("*.json"):
        target = primary / old_file.name
        if target.exists():
            continue
        try:
            old_file.rename(target)
            moved += 1
        except OSError as exc:
            logger.warning(f"迁移 {old_file} 到 {target} 失败: {exc}")
    if moved:
        logger.success(f"已从旧版 l4d2/ 目录迁移 {moved} 个文件")
    try:
        if not any(consts.LEGACY_GROUP_DIR.iterdir()):
            consts.LEGACY_GROUP_DIR.rmdir()
    except OSError:
        pass


def _rename_to_backup(path: Path) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    try:
        path.rename(backup)
    except OSError as exc:
        logger.warning(f"无法将 {path.name} 重命名为备份: {exc}")