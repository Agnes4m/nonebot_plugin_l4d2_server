from typing import Dict, List, Optional, Tuple, Union

from nonebot.log import logger

from ..l4_image import msg_to_image
from ..utils.api.models import NserverOut
from ..utils.api.request import L4API
from .draw_msg import convert_duration, draw_one_ip, get_much_server


def _get_server_json(
    command: str,
    allhost: Dict[str, List[NserverOut]],
) -> Optional[list]:
    """
    根据命令获取服务器JSON列表

    Args:
        command (str): 服务器组名
        ALLHOST (Dict): 全局服务器字典

    Returns:
        Optional[list]: 服务器JSON列表，未找到组时返回None
    """
    logger.debug(f"获取服务器组 {allhost} 的信息")
    if command:
        return allhost.get(command)
    server_json = []
    for servers in allhost.values():
        server_json.extend(servers)
    logger.debug(f"获取到的服务器组信息: {server_json}")
    return server_json


async def _handle_group_info(
    server_json: list,
    command: str,
    is_img: bool,
):
    """
    处理服务器组信息请求

    Args:
        server_json (list): 服务器JSON列表
        command (str): 服务器组名
        is_img (bool): 是否返回图片格式

    Returns:
        Union[bytes, list, None]: 图片格式返回bytes，否则返回服务器列表
    """
    logger.info(f"正在请求组服务器信息 {command}")
    server_dict = await get_much_server(server_json, command)
    if is_img:
        return await msg_to_image(server_dict)
    return server_dict


async def get_single_server_info(
    server_json: list,
    _id: str,
) -> Optional[Tuple[str, int]]:
    """
    获取单个服务器的host和port信息

    Args:
        server_json (list): 服务器JSON列表
        _id (str): 服务器ID

    Returns:
        Optional[Tuple[str, int]]: 返回(host, port)元组，未找到返回None
    """
    logger.info("正在获取单服务器信息")
    for i in server_json:
        if str(_id) == str(i["id"]):
            return i["host"], i["port"]
    return None


async def _handle_single_server(
    server_json: list,
    _id: str,
    is_img: bool,
) -> Union[bytes, str, None]:
    """
    处理单个服务器信息请求

    Args:
        server_json (list): 服务器JSON列表
        _id (str): 服务器ID
        is_img (bool): 是否返回图片格式

    Returns:
        Union[bytes, str, None]: 找到服务器时返回信息，否则返回None
    """
    server_info = await get_single_server_info(server_json, _id)
    if server_info is None:
        return None

    host, port = server_info
    return await draw_one_ip(host, port, is_img=is_img)


async def _filter_servers(
    servers: list,
    tj_mode: str,
    map_type: str = "普通药役",
) -> list:
    """筛选符合条件的服务器
    Args:
        servers: 服务器列表
        tj_mode: 筛选模式（'tj'或'zl'）
        map_type: 地图类型筛选条件
    Returns:
        符合条件的服务器列表
    """
    filtered = []
    for i in servers:
        ser_list = await L4API.a2s_info([(i["host"], i["port"])], is_player=True)
        if not ser_list:
            continue

        srv = ser_list[0][0]
        players = ser_list[0][1]

        if tj_mode == "tj" and map_type in srv.map_name:
            score = sum(p.score for p in players[:4])
            t = srv.map_name.split("[")[-1].split("特")[0]
            if t.isdigit() and int(t) * 50 < score:
                logger.info(
                    f"符合TJ条件的服务器: {i['host']}:{i['port']}, 地图: {srv.map_name}, 分数: {score}",
                )
                filtered.append(i)
        elif tj_mode == "zl" and map_type in srv.map_name and len(players) <= 4:
            logger.info(
                f"符合ZL条件的服务器: {i['host']}:{i['port']}, 地图: {srv.map_name}, 玩家数: {len(players)}",
            )
            filtered.append(i)
    return filtered


async def _format_players(player_list: list) -> str:
    """格式化玩家信息
    Args:
        player_list: 玩家对象列表
    Returns:
        格式化后的玩家信息字符串
    """
    durations = [await convert_duration(p.duration) for p in player_list]
    max_duration_len = max(len(str(d)) for d in durations)
    max_score_len = max(len(str(p.score)) for p in player_list)
    return "\n".join(
        f"[{p.score:>{max_score_len}}] | {durations[i]:^{max_duration_len}} | {p.name[0]}***{p.name[-1]}"
        for i, p in enumerate(player_list)
    )


def _build_message(srv_info, players_msg: str, selected_srv: dict, config) -> str:
    """构建服务器信息消息
    Args:
        srv_info: 服务器信息对象
        players_msg: 格式化后的玩家信息
        selected_srv: 选中的服务器信息
        config: 配置对象
    Returns:
        完整的消息字符串
    """
    msg = f"""*{srv_info.server_name}*
游戏: {srv_info.folder}
地图: {srv_info.map_name}
人数: {srv_info.player_count}/{srv_info.max_players}"""
    if srv_info.ping is not None:
        msg += f"\nping: {srv_info.ping * 1000:.0f}ms\n{players_msg}"
    if config.l4_show_ip:
        msg += f"\nconnect {selected_srv['host']}:{selected_srv['port']}"
    return msg
