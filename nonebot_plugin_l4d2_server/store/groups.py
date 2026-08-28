"""Persistence for per-tag server group JSON files.

Each group lives at ``data/L4D2/<tag>.json`` with content
``{"<tag>": [{"id": "1", "ip": "host:port"}, ...]}``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import aiofiles
import ujson as json

from nonebot_plugin_l4d2_server.consts import DEFAULT_DATA_DIR

GROUPS_DIR = Path(DEFAULT_DATA_DIR)


async def _ensure_dir() -> None:
    GROUPS_DIR.mkdir(parents=True, exist_ok=True)


def _normalize(servers: Iterable) -> list[dict]:
    """Accept dicts / strings / objects; dedup; assign string ids starting at 1."""
    seen: set[str] = set()
    items: list[dict] = []
    for s in servers or []:
        ip = ""
        if isinstance(s, str):
            ip = s.strip()
        elif isinstance(s, dict) and "ip" in s:
            ip = str(s["ip"]).strip()
        else:
            host = getattr(s, "host", None)
            port = getattr(s, "port", None)
            if host is not None and port:
                ip = f"{host}:{port}"
        if ip and ip not in seen:
            seen.add(ip)
            items.append(ip)
    return [{"id": str(i + 1), "ip": ip} for i, ip in enumerate(items)]


async def set_group(tag: str, servers: Iterable) -> Path:
    """Write ``tag``'s servers to ``data/L4D2/<tag>.json``."""
    await _ensure_dir()
    tag = str(tag).strip()
    items = _normalize(servers)
    content = json.dumps({tag: items}, ensure_ascii=False, indent=4)
    path = GROUPS_DIR / f"{tag}.json"
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content + "\n")
    return path


async def get_group(tag: str) -> list[dict]:
    """Read ``tag``'s servers, or ``[]`` if missing."""
    await _ensure_dir()
    path = GROUPS_DIR / f"{str(tag).strip()}.json"
    if not path.is_file():
        return []
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "{}")
        if isinstance(data, dict):
            return data.get(str(tag), [])
    except Exception:
        return []
    return []


async def remove_group(tag: str) -> bool:
    """Delete the per-tag JSON. Returns True if it existed."""
    await _ensure_dir()
    path = GROUPS_DIR / f"{str(tag).strip()}.json"
    if path.is_file():
        path.unlink()
        return True
    return False


async def list_groups() -> list[str]:
    """All group names (filenames without extension)."""
    await _ensure_dir()
    names: list[str] = []
    for p in GROUPS_DIR.glob("*.json"):
        if p.is_file():
            names.append(p.stem)
    names.sort()
    return names


async def export_all() -> dict[str, list[dict]]:
    """In-memory export of every group."""
    await _ensure_dir()
    result: dict[str, list[dict]] = {}
    for name in await list_groups():
        result[name] = await get_group(name)
    return result
