"""Server filtering: tj / zl / kl modes.

Implements the original ``_filter_servers`` / ``_is_tj_server`` /
``_is_zl_server`` from ``server/query/utils.py``.
"""

from __future__ import annotations

import random
from typing import List, cast

import a2s
from a2s import SourceInfo
from a2s.players import Player
from nonebot.log import logger

from api import L4API
from consts import FILTER_MODES, DEFAULT_MAP_TYPES as MAP_TYPES_DEFAULT
from messages import Sm as MsgSm
from render.images import convert_duration


def _is_tj_server(
    server_data: SourceInfo[str],
    players: List[Player],
    map_types: List[str],
) -> bool:
    """True if map type matches and score threshold is exceeded."""
    if not any(m in server_data.server_name for m in map_types):
        return False
    scores = [p.score for p in players[:4]]
    try:
        threshold = int(
            server_data.server_name.split("[")[1].split("]")[0].split("特")[0],
        )
        return threshold * 50 < sum(scores)
    except (IndexError, ValueError):
        return False


def _is_zl_server(
    server_data: SourceInfo[str],
    players: List[Player],
    map_types: List[str],
) -> bool:
    return any(m in server_data.server_name for m in map_types) and len(players) <= 4


async def filter_servers(
    servers: List[dict],
    mode: str,
    map_types: List[str] | None = None,
) -> List[dict]:
    """Return servers matching ``mode`` (``tj``, ``zl``, or ``kl``)."""
    if mode not in FILTER_MODES:
        raise ValueError(f"无效的筛选模式: {mode}")

    map_types = list(map_types or MAP_TYPES_DEFAULT)
    filtered: List[dict] = []
    for server in servers:
        info = await L4API.a2s_info_batch(
            [(server["host"], server["port"])],
        )
        if not info:
            continue
        server_data, players = info[0]
        if server_data.map_name == "无":
            continue

        if (
            (mode == "tj" and _is_tj_server(server_data, players, map_types))
            or (mode == "zl" and _is_zl_server(server_data, players, map_types))
            or (mode == "kl" and not players)
        ):
            filtered.append(server)
    return filtered


async def pick_filtered(
    servers: List[dict],
    mode: str,
) -> str:
    """Pick a random server matching ``mode`` and return its text description."""
    map_types = ["普通药役"]
    if servers is None:
        logger.warning("组不存在")
        return MsgSm.server_mistake

    logger.info(MsgSm.searching)
    try:
        matches = await filter_servers(servers, mode, map_types)
        if not matches:
            logger.warning(MsgSm.server_not_found)
            return MsgSm.server_mistake

        chosen = random.choice(matches)
        logger.info(f"最终选择的服务器: {chosen['host']}:{chosen['port']}")
        return await _describe(chosen)
    except Exception as exc:
        logger.error(f"pick_filtered error: {exc}")
        return MsgSm.other_wrong


async def _describe(server: dict) -> str:
    """Build a human-readable text description of one server."""
    info = await L4API.a2s_info_batch(
        [(server["host"], server["port"])],
    )
    if not info:
        return MsgSm.no_get
    one_server = cast(SourceInfo, info[0][0])
    one_players: List[Player] = info[0][1]

    if one_players:
        durations = [
            await convert_duration(p.duration) for p in one_players
        ]
        max_dur = max(len(d) for d in durations)
        max_score = max(len(str(p.score)) for p in one_players)
        player_lines = [
            f"[{p.score:>{max_score}}] | {durations[i]:^{max_dur}} | {p.name[0]}***{p.name[-1]}"
            for i, p in enumerate(one_players)
        ]
        player_msg = "\n".join(player_lines)
    else:
        player_msg = random.choice(MsgSm.no_player_info)

    parts = [
        f"*{one_server.server_name}*",
        f"游戏: {one_server.folder}",
        f"地图: {one_server.map_name}",
        f"人数: {one_server.player_count}/{one_server.max_players}",
    ]
    if one_server.ping is not None:
        parts.append(f"ping: {one_server.ping * 1000:.0f}ms")
        parts.append(player_msg)
    if True:  # l4_show_ip — caller decides; keep for parity
        parts.append(f"connect {server['host']}:{server['port']}")
    return "\n".join(parts)