import random
from typing import Dict, List, Optional, cast

from nonebot.log import logger

from ..config import server_all_path
from ..l4_image import msg_to_image
from ..utils.api.models import AllServer, NserverOut, OutServer
from ..utils.api.request import L4API
from ..utils.utils import split_maohao
from .draw_msg import convert_duration, draw_one_ip, get_much_server

try:
    import ujson as json
except ImportError:
    import json

from ..config import config

# 获取全部服务器信息
ALLHOST: Dict[str, List[NserverOut]] = {}
COMMAND = set()


async def get_all_server_detail():
    """
    获取所有服务器的详细信息。

    Args:
        无

    Returns:
        str: 包含所有服务器详细信息的字符串。

    """
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
        if one["max_player"]:
            out_msg += f"{one['command']} | 服务器{one['active_server']}/{one['max_server']} | 玩家{one['active_player']}/{one['max_player']}\n"
        else:
            continue
    return out_msg


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
        Union[bytes, List[OutServer], None]: 返回服务器详细信息。如果为图片格式，返回bytes类型；
                                            如果不是图片格式，返回List[OutServer]类型；如果未找到服务器组，返回None。

    """
    if command:
        server_json = ALLHOST.get(command)
    else:
        server_json = []
        for servers in ALLHOST.values():
            server_json.extend(servers)

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
    logger.info(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    logger.info("正在获取电信服务器信息")
    player_msg = ""
    right_ip = []

    async def _filter_servers(servers: list, tj_mode: str) -> list:
        """筛选符合条件的服务器
        Args:
            servers: 服务器列表
            tj_mode: 筛选模式（'tj'或'zl'）
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

    def _build_message(srv_info, players_msg: str, selected_srv: dict) -> str:
        """构建服务器信息消息
        Args:
            srv_info: 服务器信息对象
            players_msg: 格式化后的玩家信息
            selected_srv: 选中的服务器信息
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

    try:
        right_ip = await _filter_servers(server_json, tj)

        if not right_ip:
            logger.warning("没有找到符合条件的服务器")
            return "没有符合条件的服务器"

        logger.info(
            f"符合条件的服务器列表: {[f'{ip['host']}:{ip['port']}' for ip in right_ip]}",
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

        msg = _build_message(one_server, player_msg, s)
        return msg

    except Exception as e:
        logger.error(f"tj_request error: {e}")
        return "获取服务器信息时出错"
