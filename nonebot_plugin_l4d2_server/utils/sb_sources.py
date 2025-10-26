# nonebot_plugin_l4d2_server/utils/sb_sources.py
from __future__ import annotations

from pathlib import Path

import aiofiles
import ujson as json

from ..config import config

# data/L4D2/sb_pages.json : {"组名": "SourceBans服务器页URL"}
PAGES_FILE = Path(config.l4_path) / "sb_pages.json"


async def _ensure_parent():
    PAGES_FILE.parent.mkdir(parents=True, exist_ok=True)


async def load_pages() -> dict[str, str]:
    await _ensure_parent()
    if not PAGES_FILE.is_file():
        return {}
    async with aiofiles.open(PAGES_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


async def save_pages(pages: dict[str, str]) -> None:
    await _ensure_parent()
    text = json.dumps(pages, ensure_ascii=False, indent=4)
    async with aiofiles.open(PAGES_FILE, "w", encoding="utf-8") as f:
        await f.write(text + "\n")


async def get_page(tag: str) -> str | None:
    pages = await load_pages()
    return pages.get(str(tag))


async def set_page(tag: str, url: str) -> None:
    tag = str(tag).strip()
    pages = await load_pages()
    pages[tag] = url.strip()
    await save_pages(pages)


async def del_page(tag: str) -> bool:
    pages = await load_pages()
    if tag in pages:
        del pages[tag]
        await save_pages(pages)
        return True
    return False
