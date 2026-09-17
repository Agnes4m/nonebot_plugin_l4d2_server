"""Server query service: A2S queries, single-server output, group summaries."""

from __future__ import annotations

import time
from typing import List, Optional, Tuple, cast

from nonebot.log import logger

from ..api import L4API, AllServer, OutServer
from ..config import config
from ..http_helpers import split_maohao
from ..messages import Sm as MsgSm
from ..registry import registry
from ..render import render_server_card, render_server_list


async def query_group_servers(group_name: str) -> List[OutServer]:
    """Query A2S info for every server in ``group_name``."""
    servers = registry.get(group_name)
    if not servers:
        return []

    ip_list: List[Tuple[str, int]] = [(s["host"], int(s["port"])) for s in servers]
    results = await L4API.a2s_info_batch(ip_list)

    # Pad missing entries with empty SourceInfo for stable indexing.
    out: List[OutServer] = []
    for (server, players), srv in zip(results, servers):
        out.append(
            cast(
                OutServer,
                {
                    "server": server,
                    "player": players,
                    "host": srv["host"],
                    "port": srv["port"],
                    "command": group_name,
                    "id_": srv["id"],
                },
            ),
        )
    return out


def _calc_stats(servers: List[OutServer]) -> Tuple[int, int, int, int]:
    active = [s for s in servers if s["server"].max_players != 0]
    return (
        len(active),
        len(servers),
        sum(s["server"].player_count for s in active),
        sum(s["server"].max_players for s in active),
    )


def _format_summary(items: List[AllServer]) -> str:
    return "\n".join(
        f"{s['command']} | 服务器{s['active_server']}/{s['max_server']} | "
        f"玩家{s['active_player']}/{s['max_player']}"
        for s in items
        if s["max_player"]
    )


async def get_all_server_detail() -> str:
    """Aggregated summary across every loaded group."""
    items: List[AllServer] = []
    for group in registry.group_names:
        servers = await query_group_servers(group)
        if not servers:
            continue
        active, total, active_p, max_p = _calc_stats(servers)
        items.append(
            cast(
                AllServer,
                {
                    "command": group,
                    "active_server": active,
                    "max_server": total,
                    "active_player": active_p,
                    "max_player": max_p,
                },
            ),
        )
    return _format_summary(items)


async def get_server_detail(
    command: str,
    server_id: Optional[str] = None,
    *,
    is_img: bool = True,
) -> str | bytes | None:
    """Render a single server or the whole group."""
    servers = registry.get(command)
    if not servers:
        return None

    if server_id is None:
        return await _render_group(command, servers, is_img)

    endpoint = _find_endpoint(servers, server_id)
    if endpoint is None:
        return None
    host, port = endpoint
    return await _render_single(host, port, is_img)


async def _render_group(
    command: str,
    _servers: list[dict],
    is_img: bool,
) -> bytes | str:
    t_total = time.perf_counter()
    out_servers = await query_group_servers(command)
    t_after_a2s = time.perf_counter()
    a2s_ms = (t_after_a2s - t_total) * 1000
    if is_img:
        # A2S 失败时 ``server.max_players == 0`` 作 sentinel：在线画卡片，离线写文字区。
        online = [s for s in out_servers if s["server"].max_players != 0]
        offline_ids = [
            f"{s['command']}{s['id_']}"
            for s in out_servers
            if s["server"].max_players == 0
        ]
        pic = await render_server_list(online, offline_ids=offline_ids)
        render_ms = (time.perf_counter() - t_after_a2s) * 1000
        total_ms = (time.perf_counter() - t_total) * 1000
        logger.info(
            f"[l4] {command} 组查询：{len(out_servers)} 服 / "
            f"在线 {len(online)} / 不在线 {len(offline_ids)} | "
            f"A2S {a2s_ms:.0f}ms + render {render_ms:.0f}ms = {total_ms:.0f}ms"
        )
        if pic is not None:
            return pic
        # 出图超时 / 失败 / 空字节：退回文字汇总，避免 OneBot WS 心跳丢失后误判超时。
        logger.warning(f"{command} 图片渲染失败，fallback 到文字输出")
        return _format_group_text(command, out_servers)
    logger.info(
        f"[l4] {command} 组查询：{len(out_servers)} 服 / "
        f"A2S {a2s_ms:.0f}ms（仅文字模式）"
    )
    return out_servers


def _format_group_text(command: str, out_servers: List[OutServer]) -> str:
    """图片失败时的纯文字汇总：每行一台服，不带颜色 / 玩家名（避免刷屏）。"""
    lines = [f"【{command}】服务器列表（图片渲染失败，转为文字）："]
    for s in out_servers:
        srv = s["server"]
        if srv.max_players == 0:
            lines.append(f"  {s['command']}{s['id_']}  离线")
            continue
        lines.append(
            f"  {s['command']}{s['id_']}  "
            f"{srv.server_name}  "
            f"地图={srv.map_name}  "
            f"玩家={srv.player_count}/{srv.max_players}"
        )
    return "\n".join(lines)


async def _render_single(host: str, port: int, is_img: bool) -> bytes | str | None:
    info = await L4API.a2s_info_batch([(host, port)])
    if not info or info[0][0].max_players == 0:
        return MsgSm.server_outtime
    server, players = info[0]
    return await render_server_card(server, players, host, port, is_img=is_img)


def _find_endpoint(servers: list[dict], server_id: str) -> Optional[Tuple[str, int]]:
    for server in servers:
        if str(server_id) == str(server.get("id")):
            return server["host"], int(server["port"])
    return None


def find_endpoint(command: str, server_id: str) -> Optional[Tuple[str, int]]:
    """Look up ``(host, port)`` for a specific server id in ``command`` group.

    返回 ``None`` 表示该组不存在或组里没有匹配 ``server_id`` 的服务器。
    """
    servers = registry.get(command)
    if not servers:
        return None
    return _find_endpoint(servers, server_id)


async def get_ip_server(ip: str) -> bytes | str:
    """Render a server by raw ``host:port``."""
    host, port = split_maohao(ip)
    info = await L4API.a2s_info_batch([(host, port)])
    if not info or info[0][0].max_players == 0:
        return MsgSm.server_outtime
    server, players = info[0]
    return await render_server_card(server, players, host, port, is_img=config.l4_image)
