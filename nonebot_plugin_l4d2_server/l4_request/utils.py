from pathlib import Path
from typing import Dict, List, Optional, Union

from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage

from ..l4_image import msg_to_image
from ..utils.api.models import AllServer
from ..utils.api.request import L4API
from .draw_msg import convert_duration, draw_one_ip, get_much_server
from .typing import (
    DEFAULT_MAP_TYPES,
    FILTER_MODES,
    ServerDict,
    ServerInfo,
    ServerList,
    ServerStats,
)


def _get_server_json(
    command: str,
    server_registry: ServerDict,
) -> Optional[ServerList]:
    """
    根据命令获取服务器列表

    Args:
        command: 服务器组名
        server_registry: 服务器注册表

    Returns:
        服务器列表，未找到组时返回None
    """
    logger.debug(f"获取服务器组 {command} 的信息")

    if not command:
        # 返回所有服务器的扁平列表
        return [server for servers in server_registry.values() for server in servers]

    return server_registry.get(command)


async def _handle_group_info(
    servers: ServerList,
    command: str,
    use_image: bool,
) -> Union[bytes, List[Dict], None]:
    """
    处理服务器组信息请求

    Args:
        servers: 服务器列表
        command: 服务器组名
        use_image: 是否返回图片格式

    Returns:
        图片格式返回bytes，否则返回服务器列表
    """
    logger.info(f"正在请求组服务器信息 {command}")
    server_data = await get_much_server(servers, command)

    if use_image:
        return await msg_to_image(server_data)
    return server_data


async def get_server_endpoint(
    servers: ServerList,
    server_id: str,
) -> Optional[ServerInfo]:
    """
    获取单个服务器的连接端点(host:port)

    Args:
        servers: 服务器列表
        server_id: 服务器ID

    Returns:
        返回(host, port)元组，未找到返回None
    """
    logger.info(f"正在获取服务器 {server_id} 的连接信息")

    for server in servers:
        if str(server_id) == str(server["id"]):
            return server["host"], server["port"]
    return None


async def _handle_single_server(
    servers: ServerList,
    server_id: str,
    use_image: bool,
) -> Union[bytes, str, None]:
    """
    处理单个服务器信息请求

    Args:
        servers: 服务器列表
        server_id: 服务器ID
        use_image: 是否返回图片格式

    Returns:
        找到服务器时返回信息，否则返回None
    """
    endpoint = await get_server_endpoint(servers, server_id)
    if endpoint is None:
        return None

    host, port = endpoint
    return await draw_one_ip(host, port, use_image)


async def _filter_servers(
    servers: ServerList,
    filter_mode: str,
    map_types: Optional[List[str]] = None,
) -> ServerList:
    """
    根据tj等等条件筛选服务器

    Args:
        servers: 服务器列表
        filter_mode: 筛选模式（'tj'/'zl'/'kl'）
        map_types: 地图类型筛选条件

    Returns:
        符合条件的服务器列表
    """
    if filter_mode not in FILTER_MODES:
        raise ValueError(f"无效的筛选模式: {filter_mode}")

    map_types = map_types or DEFAULT_MAP_TYPES
    filtered_servers = []

    for server in servers:
        server_info = await L4API.a2s_info(
            [(server["host"], server["port"])],
            is_player=True,
        )

        if not server_info:
            continue

        server_data, players = server_info[0]

        if server_data.map_name == "无":
            continue

        server_details = (
            f"{server['host']}:{server['port']}, 地图: {server_data.map_name}"
        )

        if filter_mode == "tj":
            if await _is_tj_server(server_data, players, map_types):
                logger.info(f"符合TJ条件的服务器: {server_details}")
                filtered_servers.append(server)

        elif filter_mode == "zl":
            if await _is_zl_server(server_data, players, map_types):
                logger.info(f"符合ZL条件的服务器: {server_details}")
                filtered_servers.append(server)

        elif filter_mode == "kl" and not players:
            logger.info(f"符合KL条件的服务器: {server_details}")
            filtered_servers.append(server)

    return filtered_servers


async def _is_tj_server(server_data: Dict, players: List, map_types: List[str]) -> bool:
    """检查服务器是否符合TJ条件"""
    if not any(m in server_data.server_name for m in map_types):
        return False

    scores = [p.score for p in players[:4]]
    total_score = sum(scores)

    try:
        threshold = int(
            server_data.server_name.split("[")[1].split("]")[0].split("特")[0],
        )
        return threshold * 50 < total_score
    except (IndexError, ValueError):
        return False


async def _is_zl_server(server_data: Dict, players: List, map_types: List[str]) -> bool:
    """检查服务器是否符合ZL条件"""
    return any(m in server_data.server_name for m in map_types) and len(players) <= 4


async def _format_players(players: List[Dict]) -> str:
    """
    格式化玩家信息为可读字符串

    Args:
        players: 玩家对象列表

    Returns:
        格式化后的玩家信息字符串
    """
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
    server_data: Dict,
    players_info: str,
    selected_server: Dict,
    show_ip: bool,
) -> str:
    """
    构建完整的服务器信息消息

    Args:
        server_data: 服务器信息
        players_info: 玩家信息字符串
        selected_server: 选中的服务器
        show_ip: 是否显示连接信息

    Returns:
        格式化后的消息字符串
    """
    message = [
        f"*{server_data.server_name}*",
        f"游戏: {server_data.folder}",
        f"地图: {server_data.map_name}",
        f"人数: {server_data.player_count}/{server_data.max_players}",
    ]

    if server_data.ping is not None:
        message.append(f"ping: {server_data.ping * 1000:.0f}ms")
        message.append(players_info)

    if show_ip:
        message.append(f"connect {selected_server['host']}:{selected_server['port']}")

    return "\n".join(message)


def _calculate_server_stats(servers: List[Dict]) -> ServerStats:
    """
    计算服务器组的统计指标

    Args:
        servers: 服务器组详细信息列表

    Returns:
        ServerStats对象包含统计信息
    """
    active_servers = sum(1 for s in servers if s["server"].max_players != 0)
    total_servers = len(servers)
    active_players = sum(
        s["server"].player_count for s in servers if s["server"].max_players != 0
    )
    max_players = sum(
        s["server"].max_players for s in servers if s["server"].max_players != 0
    )

    return ServerStats(active_servers, total_servers, active_players, max_players)


def _format_server_summary(servers: List[AllServer]) -> str:
    """
    格式化服务器摘要信息

    Args:
        servers: 服务器信息列表

    Returns:
        格式化后的多行字符串
    """
    return "\n".join(
        f"{srv['command']} | 服务器{srv['active_server']}/{srv['max_server']} | "
        f"玩家{srv['active_player']}/{srv['max_player']}"
        for srv in servers
        if srv["max_player"]
    )


def _update_global_state(
    group_name: str,
    servers: List[dict],
    item: Path,
) -> None:
    """
    更新全局状态并记录日志

    参数:
        group_name: 服务器组名称
        servers: 处理后的服务器配置列表
    输出:
        无，直接修改全局变量ALLHOST和COMMAND
    """
    global ALLHOST, COMMAND
    ALLHOST.update({group_name: servers})
    COMMAND.add(group_name)
    logger.success(
        f"成功加载 {item.name.split('.')[0]} {len(servers)}个",
    )


async def _handle_single_server_with_endpoint(
    use_image: bool,
    host: str,
    port: int,
) -> Union[bytes, str, None]:
    """
    处理单个服务器信息请求（已获取端点信息）

    Args:
        servers: 服务器列表
        server_id: 服务器ID
        use_image: 是否返回图片格式
        host: 服务器主机地址
        port: 服务器端口

    Returns:
        找到服务器时返回信息，否则返回None
    """
    msg = await draw_one_ip(host, port, use_image)
    if isinstance(msg, bytes):
        await (
            UniMessage.image(raw=msg) + UniMessage.text(f"connect {host}:{port}")
        ).finish()
    return msg
