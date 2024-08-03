from typing import Dict, List, Optional, cast

from nonebot.log import logger

from ..config import server_all_path
from ..l4_image import msg_to_image
from ..utils.api.models import AllServer, NserverOut, OutServer
from ..utils.utils import split_maohao
from .draw_msg import draw_one_ip, get_much_server

try:
    import ujson as json
except ImportError:
    import json


# 获取全部服务器信息
ALLHOST: Dict[str, List[NserverOut]] = {}
COMMAND = set()


async def get_all_server_detail():
    out_list: List[AllServer] = []
    for group in ALLHOST:
        msg_list = await get_group_detail(group)
        if msg_list is None:
            continue
        active_server = 0
        max_server = 0
        active_player = 0
        max_player = 0
        for index, msg in enumerate(msg_list):
            max_server = index + 1
            if msg["server"].max_players != 0:
                active_server += 1
                active_player += msg["server"].player_count
                max_player += msg["server"].max_players
        data = {
            "command": group,
            "active_server": active_server,
            "max_server": max_server,
            "active_player": active_player,
            "max_player": max_player,
        }
        out_list.append(cast(AllServer, data))

    # to do作图，先用文字凑合
    out_msg = ""
    for one in out_list:
        out_msg += f"{one['command']} | 服务器{one['active_server']}/{one['max_server']} | 玩家{one['active_player']}/{one['max_player']}\n"
    return out_msg


async def get_server_detail(
    command: str,
    _id: Optional[str] = None,
    is_img: bool = True,
):
    server_json = ALLHOST.get(command)
    logger.info(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    if _id is None:
        # 输出组信息
        logger.info(f"正在请求组服务器信息 {command}")
        server_dict = await get_much_server(server_json, command)
        if is_img:
            out_msg = await msg_to_image(server_dict)
        else:
            out_msg = server_dict
        return out_msg

    # 返回单个
    logger.info("正在请求单服务器信息")
    out_msg = ""
    for i in server_json:
        if str(_id) == str(i["id"]):
            out_msg = await draw_one_ip(i["host"], i["port"])
            if is_img:
                return cast(bytes, out_msg)
            if not is_img:
                return cast(List[OutServer], out_msg)
    # print(out_msg)
    return None


async def get_group_detail(
    command: str,
):
    server_json = ALLHOST.get(command)
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
    # print("正在读取json文件")
    group_ip = []
    for item in server_all_path.iterdir():
        if item.is_file():
            if item.name.endswith("json"):
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

            if item.name.endswith("txt"):
                """to do"""
