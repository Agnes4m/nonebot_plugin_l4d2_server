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

    try:
        for i in server_json:
            ser_list = await L4API.a2s_info([(i["host"], i["port"])], is_player=True)
            if not ser_list:
                continue

            one_server = ser_list[0][0]
            one_player = ser_list[0][1]

            if tj == "tj" and map_type in one_server.map_name:
                score = sum(p.score for p in one_player[:4])
                t = one_server.map_name.split("[")[-1].split("特")[0]
                if t.isdigit() and int(t) * 50 < score:
                    logger.info(
                        f"符合TJ条件的服务器: {i['host']}:{i['port']}, 地图: {one_server.map_name}, 分数: {score}",
                    )
                    right_ip.append(i)
            elif (
                tj == "zl" and map_type in one_server.map_name and len(one_player) <= 4
            ):
                logger.info(
                    f"符合ZL条件的服务器: {i['host']}:{i['port']}, 地图: {one_server.map_name}, 玩家数: {len(one_player)}",
                )
                right_ip.append(i)

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
            durations = [await convert_duration(p.duration) for p in one_player]
            max_duration_len = max(len(str(d)) for d in durations)
            max_score_len = max(len(str(p.score)) for p in one_player)

            durations = [await convert_duration(p.duration) for p in one_player]
            player_msg = "\n".join(
                f"[{p.score:>{max_score_len}}] | {durations[i]:^{max_duration_len}} | {p.name[0]}***{p.name[-1]}"
                for i, p in enumerate(one_player)
            )
        else:
            player_msg = "服务器感觉很安静啊"

        msg = f"""*{one_server.server_name}*
游戏: {one_server.folder}
地图: {one_server.map_name}
人数: {one_server.player_count}/{one_server.max_players}"""

        if one_server.ping is not None:
            msg += f"\nping: {one_server.ping * 1000:.0f}ms\n{player_msg}"
        if config.l4_show_ip:
            msg += f"\nconnect {s['host']}:{s['port']}"
        else:
            return msg

    except Exception as e:
        logger.error(f"tj_request error: {e}")
        return "获取服务器信息时出错"
