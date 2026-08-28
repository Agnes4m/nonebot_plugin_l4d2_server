"""SourceBans++ refresh orchestration. business logic and the inline
``sync_sb_pages_groups`` from ``__main__.py``.
"""

from __future__ import annotations

from typing import List

from nonebot.log import logger

from ..api import L4API, SourceBansInfo
from ..registry import registry
from ..store import groups as groups_store
from ..store import pages as pages_store


async def refresh_group_from_url(tag: str, url: str) -> List[SourceBansInfo]:
    """Scrape a SourceBans URL and persist as ``tag``'s server list."""
    api = L4API
    servers = await api.get_sourceban(tag, url)
    path = await groups_store.set_group(tag, servers)
    await reload_registry()
    logger.success(f"已更新 {path.name}（共 {len(servers)} 台）")
    return servers


async def refresh_all_pages() -> tuple[int, list[str]]:
    """Re-fetch every URL stored in ``sb_pages.json``.

    Returns ``(success_count, failures)``.
    """
    pages = await pages_store.load_pages()
    ok = 0
    failures: list[str] = []
    for tag, url in pages.items():
        try:
            await refresh_group_from_url(tag, url)
            ok += 1
        except Exception as exc:
            failures.append(f"{tag}: {exc}")
    return ok, failures


async def reload_registry() -> None:
    """Re-scan server JSON files into the in-memory registry."""
    await registry.load_all()


def register_anne_alias() -> None:
    """Always-available ``anne`` command alias."""
    registry.add_command("anne")
