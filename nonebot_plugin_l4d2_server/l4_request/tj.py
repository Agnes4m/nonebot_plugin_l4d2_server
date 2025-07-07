import random

from nonebot.log import logger

from ..config import config
from ..utils.api.request import L4API
from .typing import ALLHOST
from .utils import (
    _filter_servers,
    _format_players,
    build_server_message,
)


async def tj_request(command: str = "云", tj="tj"):
    map_type = "普通药役"
    server_json = ALLHOST.get(command)
    logger.debug(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    logger.info("正在获取电信服务器信息")
    right_ip = []

    try:
        right_ip = await _filter_servers(server_json, tj, map_type)

        if not right_ip:
            logger.warning("没有找到符合条件的服务器")
            return "没有符合条件的服务器"

        server_list_str = [f"{ip['host']}:{ip['port']}" for ip in right_ip]
        logger.info(
            f"符合条件的服务器列表: {server_list_str}",
        )
        # 获取服务器信息并构建响应消息
        return await _get_server_info_and_build(right_ip, config)

    except Exception as e:
        logger.error(f"tj_request error: {e}")
        return "获取服务器信息时出错"


async def _get_server_info_and_build(server_list: list, config) -> str:
    """
    从服务器列表中随机选择服务器，获取信息并构建响应消息

    参数:
        server_list: 符合条件的服务器列表
        config: 配置对象

    返回:
        str: 格式化后的服务器信息响应消息
    """
    s = random.choice(server_list)
    logger.info(f"最终选择的服务器: {s['host']}:{s['port']}")
    ser_list = await L4API.a2s_info([(s["host"], s["port"])], is_player=True)
    if not ser_list:
        return "获取服务器信息失败"

    one_server = ser_list[0][0]
    one_player = ser_list[0][1]

    if one_player:
        player_msg = await _format_players(one_player)
    else:
        player_msg = "服务器感觉很安静啊"

    return build_server_message(one_server, player_msg, s, config)
