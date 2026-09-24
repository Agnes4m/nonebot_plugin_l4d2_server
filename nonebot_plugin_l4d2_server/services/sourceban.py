"""SourceBans++ refresh orchestration. business logic and the inline
``sync_sb_pages_groups`` from ``__main__.py``.
"""

from __future__ import annotations

import asyncio
from typing import List

from nonebot.log import logger

from ..api import L4API, SourceBansInfo
from ..config import config
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
    """并发刷新 ``sb_pages.json`` 里所有 URL。

    并发上限复用 ``config.l4_a2s_concurrency``（语义一致：都是对外部 HTTP 抓取
    限流）。单个组失败不阻塞其他组，失败信息汇总到返回列表。
    """
    pages = await pages_store.load_pages()
    if not pages:
        return 0, []

    sem = asyncio.Semaphore(max(1, int(config.l4_a2s_concurrency)))

    async def _one(tag: str, url: str) -> tuple[str, str | None]:
        async with sem:
            try:
                await refresh_group_from_url(tag, url)
            except Exception as exc:
                logger.warning(f"SourceBans 刷新失败 [{tag}]: {exc}")
                return tag, f"{tag}: {exc}"
            else:
                return tag, None

    results = await asyncio.gather(*[_one(t, u) for t, u in pages.items()])
    failures = [m for _, m in results if m is not None]
    ok = sum(1 for _, m in results if m is None)
    return ok, failures


async def reload_registry() -> None:
    """Re-scan server JSON files into the in-memory registry."""
    await registry.load_all()


def register_anne_alias() -> None:
    """Always-available ``anne`` command alias."""
    registry.add_command("anne")
