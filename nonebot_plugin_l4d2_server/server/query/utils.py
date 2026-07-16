from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from a2s import SourceInfo
from a2s.players import Player
from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage

from ...presentation.render import msg_to_image
from ...shared.utils.api.models import AllServer, OutServer
from ...shared.utils.api.request import L4API
from .draw_msg import convert_duration, draw_one_ip, get_much_server
from .typing import (
    ALLHOST,
    COMMAND,
    DEFAULT_MAP_TYPES,
    FILTER_MODES,
    ServerDict,
    ServerInfo,
    ServerList,
)


def _get_server_json(
    command: str,
    server_registry: ServerDict,
) -> Optional[ServerList]:
    logger.debug(f"获取服务器组 {command} 的信息")
    if not command:
        return [server for servers in server_registry.values() for server in servers]
    return server_registry.get(command)


async def _handle_group_info(
    servers: ServerList,
    command: str,
    use_image: bool,
) -> Union[bytes, List[OutServer], None]:
    server_data = await get_much_server(servers, command)
    if use_image:
        return await msg_to_image(server_data)
    return server_data


async def get_server_endpoint(
    servers: ServerList,
    server_id: str,
) -> Optional[ServerInfo]:
    for server in servers:
        if str(server_id) == str(server["id"]):
            return server["host"], server["port"]
    return None


async def _handle_single_server(
    servers: ServerList,
    server_id: str,
    use_image: bool,
) -> Union[bytes, str, None]:
    endpoint = await get_server_endpoint(servers, server_id)
    if endpoint is None:
        return None
    return await draw_one_ip(endpoint[0], endpoint[1], use_image)


async def _filter_servers(
    servers: ServerList,
    filter_mode: str,
    map_types: Optional[List[str]] = None,
) -> ServerList:
    if filter_mode not in FILTER_MODES:
        raise ValueError(f"无效的筛选模式: {filter_mode}")

    map_types = map_types or DEFAULT_MAP_TYPES
    filtered = []
    for server in servers:
        info = await L4API.a2s_info([(server["host"], server["port"])], is_player=True)
        if not info:
            continue
        server_data, players = info[0]
        if server_data.map_name == "无":
            continue

        if (
            (
                filter_mode == "tj"
                and await _is_tj_server(server_data, players, map_types)
            )
            or (
                filter_mode == "zl"
                and await _is_zl_server(server_data, players, map_types)
            )
            or (filter_mode == "kl" and not players)
        ):
            filtered.append(server)
    return filtered


async def _is_tj_server(
    server_data: SourceInfo[str],
    players: List,
    map_types: List[str],
) -> bool:
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


async def _is_zl_server(
    server_data: SourceInfo[str],
    players: List,
    map_types: List[str],
) -> bool:
    return any(m in server_data.server_name for m in map_types) and len(players) <= 4


async def _format_players(players: List[Player[Any]]) -> str:
    if not players:
        return "无玩家在线"
    durations = [await convert_duration(p.duration) for p in players]
    max_duration_len = max(len(str(d)) for d in durations)
    max_score_len = max(len(str(p.score)) for p in players)
    return "\n".join(
        f"[{p.score:>{max_score_len}}] | {durations[i]:^{max_duration_len}} | {p.name[0]}***{p.name[-1]}"
        for i, p in enumerate(players)
    )


def build_server_message(
    server_data: SourceInfo[Any],
    players_info: str,
    selected_server: Dict,
    show_ip: bool,
) -> str:
    msg = [
        f"*{server_data.server_name}*",
        f"游戏: {server_data.folder}",
        f"地图: {server_data.map_name}",
        f"人数: {server_data.player_count}/{server_data.max_players}",
    ]
    if server_data.ping is not None:
        msg.append(f"ping: {server_data.ping * 1000:.0f}ms")
        msg.append(players_info)
    if show_ip:
        msg.append(f"connect {selected_server['host']}:{selected_server['port']}")
    return "\n".join(msg)


def _calculate_server_stats(servers: List[OutServer]) -> Tuple[int, int, int, int]:
    active = [s for s in servers if s["server"].max_players != 0]
    return (
        len(active),
        len(servers),
        sum(s["server"].player_count for s in active),
        sum(s["server"].max_players for s in active),
    )


def _format_server_summary(servers: List[AllServer]) -> str:
    return "\n".join(
        f"{s['command']} | 服务器{s['active_server']}/{s['max_server']} | "
        f"玩家{s['active_player']}/{s['max_player']}"
        for s in servers
        if s["max_player"]
    )


def _update_global_state(
    group_name: str,
    servers: ServerList,
    item: Path,
) -> None:
    global ALLHOST, COMMAND
    ALLHOST[group_name] = servers
    COMMAND.add(group_name)
    logger.success(f"成功加载 {item.stem} {len(servers)}个")


async def _handle_single_server_with_endpoint(
    use_image: bool,
    host: str,
    port: int,
) -> Union[bytes, str, None]:
    msg = await draw_one_ip(host, port, use_image)
    if isinstance(msg, bytes):
        await (
            UniMessage.image(raw=msg) + UniMessage.text(f"connect {host}:{port}")
        ).finish()
    return msg
