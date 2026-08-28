"""Server query service: A2S queries, single-server output, group summaries.

Replaces the ``get_server_detail`` / ``get_group_detail`` /
``get_all_server_detail`` / ``get_ip_server`` functions previously in
``server/query/__init__.py``.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, cast

from config import config  # injected at runtime
from api import L4API, AllServer, OutServer
from messages import Sm as MsgSm
from registry import registry
from render import render_server_card, render_server_list
from http_helpers import split_maohao


async def query_group_servers(group_name: str) -> List[OutServer]:
    """Query A2S info for every server in ``group_name``."""
    servers = registry.get(group_name)
    if not servers:
        return []

    ip_list: List[Tuple[str, int]] = [
        (s["host"], int(s["port"])) for s in servers
    ]
    results = await L4API.a2s_info_batch(ip_list)

    # Pad missing entries with empty SourceInfo for stable indexing.
    out: List[OutServer] = []
    for idx, ((server, players), srv) in enumerate(zip(results, servers)):
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
    servers: list[dict],
    is_img: bool,
) -> bytes | list[OutServer]:
    out_servers = await query_group_servers(command)
    if is_img:
        return await render_server_list(out_servers)
    return out_servers


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


async def get_ip_server(ip: str) -> bytes | str:
    """Render a server by raw ``host:port``."""
    host, port = split_maohao(ip)
    info = await L4API.a2s_info_batch([(host, port)])
    if not info or info[0][0].max_players == 0:
        return MsgSm.server_outtime
    server, players = info[0]
    return await render_server_card(server, players, host, port, is_img=config.l4_image)