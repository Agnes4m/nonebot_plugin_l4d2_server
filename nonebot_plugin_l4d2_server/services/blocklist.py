"""关键词屏蔽（README「屏蔽与关键词」方案 4）。

``config.l4_block_keywords`` 是一组正则（不区分大小写），在 A2S 结果和
输出之间过滤：

- 服务器名命中：整台服务器不出现在组查询、查人、tj/zl/kl 等结果里，
  单服 / connect 查询只回「已被屏蔽」。
- 玩家名命中：只隐藏这个玩家，服务器照常显示，人数仍按 A2S 上报。

非法正则记一条警告后跳过，不影响其它关键词。
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Tuple

from a2s.players import Player
from nonebot.log import logger

from ..config import config


@lru_cache(maxsize=8)
def _compile(patterns: Tuple[str, ...]) -> Tuple[re.Pattern[str], ...]:
    compiled: List[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error as exc:
            logger.warning(
                f"[l4] l4_block_keywords 里的 {pattern!r} 不是合法正则，已忽略: {exc}",
            )
    return tuple(compiled)


def _patterns() -> Tuple[re.Pattern[str], ...]:
    return _compile(tuple(p for p in config.l4_block_keywords if p))


def is_blocked(name: str) -> bool:
    """``name`` 命中任意屏蔽关键词。"""
    return any(p.search(name or "") for p in _patterns())


def visible_players(players: List[Player]) -> List[Player]:
    """去掉名字命中屏蔽关键词的玩家；没配置关键词时原样返回。"""
    if not _patterns():
        return players
    return [p for p in players if not is_blocked(p.name)]
