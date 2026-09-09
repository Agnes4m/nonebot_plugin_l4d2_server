"""Persistence for SourceBans URL map (``sb_pages.json``).

Single source of truth: ``<l4_path>/sb_pages.json`` (default
``data/L4D2/sb_pages.json``) with content
``{"组名": "https://sb.example.com/"}``.
"""

from __future__ import annotations

from pathlib import Path

import aiofiles
import ujson as json

from ..config import config
from ..consts import SB_PAGES_FILENAME


def pages_file() -> Path:
    """运行时权威的 sb_pages.json 路径（来自 ``config.l4_path``）。"""
    return config.data_dir / SB_PAGES_FILENAME


async def _ensure_parent() -> None:
    pages_file().parent.mkdir(parents=True, exist_ok=True)


async def load_pages() -> dict[str, str]:
    """Return the full URL map, or ``{}`` if missing/invalid."""
    await _ensure_parent()
    target = pages_file()
    if not target.is_file():
        return {}
    async with aiofiles.open(target, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


async def save_pages(pages: dict[str, str]) -> None:
    """Overwrite the URL map."""
    await _ensure_parent()
    text = json.dumps(pages, ensure_ascii=False, indent=4)
    async with aiofiles.open(pages_file(), "w", encoding="utf-8") as f:
        await f.write(text + "\n")


async def get_page(tag: str) -> str | None:
    return (await load_pages()).get(str(tag))


async def set_page(tag: str, url: str) -> None:
    """Add or replace ``tag``'s URL."""
    tag = str(tag).strip()
    pages = await load_pages()
    pages[tag] = url.strip()
    await save_pages(pages)


async def del_page(tag: str) -> bool:
    """Remove ``tag``. Returns True if it was present."""
    pages = await load_pages()
    if tag in pages:
        del pages[tag]
        await save_pages(pages)
        return True
    return False
