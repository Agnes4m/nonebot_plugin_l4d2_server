"""跨服模糊查人。

``l4查人 <玩家名>``：并发查所有组的服务器（``registry.get_groups()`` 全跑），
返回玩家名匹配（模糊匹配，容忍空格 / emoji / tag）的结果。

输出：命中 ≤ 4 个直接列；> 4 个给精简文本菜单，提示 ``l4 <组> <id>`` 看详情。
"""

from __future__ import annotations

import difflib
from typing import Iterable

from a2s.players import Player
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from ..api import L4API
from ..registry import registry
from ..services.errors import L4Error, L4InvalidInputError

l4_find_player = on_command(
    "l4查人",
    aliases={"l4_findplayer", "l4findplayer"},
    permission=SUPERUSER,
)

# 模糊匹配阈值：1.0 = 完全相等；<0.6 通常是噪声
FUZZY_THRESHOLD = 0.55
# 命中展示上限：超过转文本菜单
MAX_INLINE_HITS = 4


def _norm(name: str) -> str:
    """归一化玩家名：去首尾空白、压多空格、忽略空字节；不改变大小写以便模糊。"""
    return " ".join((name or "").split())


def _match_score(query: str, candidate: str) -> float:
    """``difflib.SequenceMatcher.ratio()``，返回 0-1。"""
    if not query or not candidate:
        return 0.0
    q = _norm(query).lower()
    c = _norm(candidate).lower()
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    # 短串做包含检查（"a" 在 "abc" 里 → 1.0），否则 ratio
    if q in c:
        return 1.0
    return difflib.SequenceMatcher(None, q, c).ratio()


async def _collect(server_dict: list[dict]) -> Iterable[tuple[dict, list[Player]]]:
    """并发查 ``server_dict`` 内所有服，返回 ``(server_meta, players)`` 流。"""
    ips: list[tuple[str, int]] = [(s["host"], int(s["port"])) for s in server_dict]
    if not ips:
        return
    results = await L4API.a2s_info_batch(ips, want_players=True)
    for (server, players), srv in zip(results, server_dict):
        yield srv, server, players


def _format_hits(query: str, hits: list[tuple[dict, str, int, int, int]]) -> str:
    """``hits`` = [(server_entry, server_name, player_count, max_players, idx_in_group)]."""
    lines = [f"「{query}」找到 {len(hits)} 处："]
    for entry, server_name, pc, mp, idx in hits:
        tag = entry.get("tag")
        sid = entry.get("id")
        lines.append(
            f"  [{tag}{sid}] {entry.get('ip')}  {server_name}  {pc}/{mp}",
        )
    lines.append("")
    lines.append("查看详情：``l4 <组> <id>`` 或 ``l4 <组>``")
    return "\n".join(lines)


@l4_find_player.handle()
async def _(args: Message = CommandArg()) -> None:
    try:
        query = args.extract_plain_text().strip()
        if not query:
            raise L4InvalidInputError("用法：l4查人 <玩家名>")
    except L4Error as exc:
        await UniMessage.text(str(exc)).finish()
        return

    # 全服并发查；want_players=True 才能拿到玩家名
    all_servers: list[dict] = []
    for tag in registry.group_names:
        for entry in registry.get(tag) or []:
            entry = dict(entry)
            entry["tag"] = tag
            all_servers.append(entry)

    if not all_servers:
        await UniMessage.text("❌ 没有任何已加载的服务器组").finish()
        return

    hits: list[tuple[dict, str, int, int, int]] = []
    try:
        async for entry, server, players in _collect(all_servers):
            if not players:
                continue
            for idx_in_group, p in enumerate(players):
                score = _match_score(query, p.name)
                if score >= FUZZY_THRESHOLD:
                    hits.append(
                        (
                            entry,
                            str(getattr(server, "server_name", "") or ""),
                            int(getattr(server, "player_count", 0) or 0),
                            int(getattr(server, "max_players", 0) or 0),
                            idx_in_group,
                        )
                    )
    except Exception as exc:
        await UniMessage.text(f"❌ 查询失败：{exc}").finish()
        return

    if not hits:
        await UniMessage.text(
            f"「{query}」未在任何服务器中找到（阈值 {FUZZY_THRESHOLD}）。"
            f"玩家名含特殊字符 / 全角符号可能匹配不上。",
        ).finish()
        return

    # 按 tag+id 排序去重（同服只保留分数最高的一次）
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[dict, str, int, int, int]] = []
    for h in hits:
        key = (h[0].get("tag"), h[0].get("id"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(h)

    if len(deduped) <= MAX_INLINE_HITS:
        await UniMessage.text(_format_hits(query, deduped)).finish()
        return

    # 超过阈值给摘要 + 提示
    sample = deduped[:MAX_INLINE_HITS]
    extra = len(deduped) - MAX_INLINE_HITS
    lines = _format_hits(query, sample).splitlines()
    lines.append(f"... 还有 {extra} 个匹配未列出（请用更精确的名字）。")
    await UniMessage.text("\n".join(lines)).finish()
