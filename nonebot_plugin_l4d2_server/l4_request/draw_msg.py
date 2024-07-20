import asyncio
from typing import List

import a2s

from ..utils.api.models import NserverOut, OutServer
from ..utils.api.request import L4API


async def draw_one_ip(host: str, port: int):
    """输出单个ip"""
    # 先用文字凑合
    try:
        one_server = await L4API.a2s_info(host, port)
        one_player = await L4API.a2s_players(host, port)
        print(one_player)
    except asyncio.exceptions.TimeoutError:
        return "服务器无响应"
    player_msg = ""
    if len(one_player):
        max_duration_len = max([len(str(i.duration)) for i in one_player])
        max_score_len = max([len(str(i.score)) for i in one_player])

        for player in one_player:
            soc = "[{:>{}}]".format(player.score, max_score_len)
            chines_dur = await convert_duration(player.duration)
            dur = "{:^{}}".format(chines_dur, max_duration_len)

            player_msg += f"{soc} | {dur} | {player.name} \n"
    else:
        player_msg = "服务器感觉很安静啊"

    return f""" 【{one_server.server_name}】
游戏: {one_server.folder}
地图: {one_server.map_name}
ping: {one_server.ping*1000:.0f}ms
{player_msg}
connect: {host}:{port}
"""


async def get_much_server(server_json: List[NserverOut], command):
    out_server: List[OutServer] = []
    for i in server_json:
        try:
            one_server = await L4API.a2s_info(i["host"], i["port"])
            one_player = await L4API.a2s_players(i["host"], i["port"])
            print(one_player)
            out_server.append(
                {
                    "server": one_server,
                    "player": one_player,
                    "host": i["host"],
                    "port": i["port"],
                    "command": command,
                    "id_": i["id"],
                },
            )

        except asyncio.exceptions.TimeoutError:
            emtry_server = a2s.SourceInfo()
            emtry_server.server_name = "服务器无响应"
            emtry_server.map_name = "无"
            emtry_server.player_count = 0
            emtry_server.max_players = 0
            out_server.append(
                {
                    "server": emtry_server,
                    "player": [],
                    "host": i["host"],
                    "port": i["port"],
                    "command": command,
                    "id_": i["id"],
                },
            )  # type: ignore
    return out_server


async def convert_duration(duration: float) -> str:
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    time_str = ""
    if hours > 0:
        time_str += f"{int(hours)}h "
    if minutes > 0:
        time_str += f"{int(minutes)}m "
    time_str += f"{int(seconds)}s"
    return time_str
    time_str += f"{int(seconds)}s"
    return time_str
