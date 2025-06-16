import random
from typing import Dict, List, Optional, cast

from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage

from ..config import config, server_all_path
from ..utils.api.models import AllServer, NserverOut
from ..utils.api.request import L4API
from ..utils.utils import split_maohao
from .draw_msg import draw_one_ip, get_much_server
from .utils import (
    _build_message,
    _filter_servers,
    _format_players,
    _get_server_json,
    _handle_group_info,
    _handle_single_server,
    get_single_server_info,
)

try:
    import ujson as json
except ImportError:
    import json


# 获取全部服务器信息
ALLHOST: Dict[str, List[NserverOut]] = {}
COMMAND = set()


async def get_all_server_detail() -> str:
    """
    获取所有服务器的详细信息。

    Returns:
        str: 包含所有服务器详细信息的字符串。
    """
    out_list: List[AllServer] = []
    for group in ALLHOST:
        msg_list = await get_group_detail(group)
        if not msg_list:
            continue

        active_server = sum(1 for msg in msg_list if msg["server"].max_players != 0)
        max_server = len(msg_list)
        active_player = sum(
            msg["server"].player_count
            for msg in msg_list
            if msg["server"].max_players != 0
        )
        max_player = sum(
            msg["server"].max_players
            for msg in msg_list
            if msg["server"].max_players != 0
        )

        data = {
            "command": group,
            "active_server": active_server,
            "max_server": max_server,
            "active_player": active_player,
            "max_player": max_player,
        }
        out_list.append(cast(AllServer, data))

    # 输出服务器信息文本
    return "\n".join(
        f"{one['command']} | 服务器{one['active_server']}/{one['max_server']} | 玩家{one['active_player']}/{one['max_player']}"
        for one in out_list
        if one["max_player"]
    )


async def get_server_detail(
    command: str = "",
    _id: Optional[str] = None,
    is_img: bool = True,
):
    """
    异步获取服务器详细信息。

    Args:
        command (str): 服务器组名。
        _id (Optional[str], optional): 服务器ID。默认为None。
        is_img (bool, optional): 是否返回图片格式的信息。默认为True。

    Returns:
        Union[UniMessage, None]:
            返回服务器详细信息（图片或文本格式），未找到服务器组或服务器时返回None。
    """
    server_json = _get_server_json(command, ALLHOST)
    logger.info(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    # 输出组服务器信息
    if _id is None:
        return await _handle_group_info(server_json, command, is_img)

    _ip = await get_single_server_info(server_json, _id)
    if _ip is None:
        logger.warning("未找到这个服务器")
        return None

    out_msg = await _handle_single_server(server_json, _id, is_img)
    if isinstance(out_msg, bytes):
        return UniMessage.image(raw=out_msg) + UniMessage.text(
            f"connect {_ip[0]}:{_ip[1]}",
        )
    if isinstance(out_msg, str):
        return UniMessage.text(out_msg)
    return None


async def get_group_detail(
    command: str,
):
    server_json = _get_server_json(command, ALLHOST)
    # logger.debug(f"获取组服务器信息: {server_json}")
    logger.info(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    logger.info("正在请求组服务器信息")
    return await get_much_server(server_json, command)


async def get_ip_server(ip: str):
    host, port = split_maohao(ip)
    return await draw_one_ip(host, port)


# 以下是重载ip
def reload_ip():
    global COMMAND
    group_ip = []
    for item in server_all_path.iterdir():
        if item.is_file() and item.name.endswith("json"):
            json_data = json.loads(item.read_text(encoding="utf-8"))
            group_server = cast(Dict[str, List[NserverOut]], json_data)

            for group, group_ip in group_server.items():
                # 处理ip,host,port关系
                for one_ip in group_ip:
                    if one_ip.get("ip"):
                        if one_ip.get("host") and one_ip.get("port"):
                            pass
                        if one_ip.get("host") and not one_ip.get("port"):
                            one_ip["port"] = 20715
                        if not one_ip.get("host"):
                            one_ip["host"], one_ip["port"] = split_maohao(
                                one_ip.get("ip"),
                            )
                    else:
                        if one_ip.get("host") and one_ip.get("port"):
                            one_ip["ip"] = f'{one_ip["host"]}:{one_ip["port"]}'
                        if one_ip.get("host") and not one_ip.get("port"):
                            one_ip["ip"] = f'{one_ip["host"]}:20715'
                        else:
                            logger.warning(f"{one_ip} 没有ip")

                ALLHOST.update({group: group_ip})
                COMMAND.add(group)
            logger.success(f"成功加载 {item.name.split('.')[0]} {len(group_ip)}个")


async def tj_request(command: str = "云", tj="tj"):
    map_type = "普通药役"
    server_json = ALLHOST.get(command)
    logger.debug(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    logger.info("正在获取电信服务器信息")
    player_msg = ""
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
        s = random.choice(right_ip)
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

        return _build_message(one_server, player_msg, s, config)

    except Exception as e:
        logger.error(f"tj_request error: {e}")
        return "获取服务器信息时出错"


async def server_find(
    command: str = "",
    _id: Optional[str] = None,
    is_img: bool = True,
):
    all_command = get_all_json_filenames()
    server_json = []
    for one_command in all_command:
        server_j = _get_server_json(one_command, ALLHOST)
        server_json.extend(server_j)
    logger.info(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    # 输出组服务器信息
    if _id is None:
        return await _handle_group_info(server_json, command, is_img)

    _ip = await get_single_server_info(server_json, _id)
    if _ip is None:
        logger.warning("未找到这个服务器")
        return None

    out_msg = await _handle_single_server(server_json, _id, is_img)
    if isinstance(out_msg, bytes):
        return UniMessage.image(raw=out_msg) + UniMessage.text(
            f"connect {_ip[0]}:{_ip[1]}",
        )
    if isinstance(out_msg, str):
        return UniMessage.text(out_msg)
    return None


def get_all_json_filenames():
    """
    获取 server_all_path 路径下所有 json 文件的文件名（不带扩展名）的列表。
    """
    json_files = []
    for item in server_all_path.iterdir():
        if item.is_file() and item.suffix == ".json":
            json_files.append(item.stem)
    return json_files


# 使用示例

# all_json_names 现在是一个包含所有 json 文件名（不带扩展名）的 list
