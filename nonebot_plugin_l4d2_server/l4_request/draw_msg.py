import asyncio

# from logging import log
from typing import List, Tuple

from ..config import config
from ..utils.api.models import NserverOut, OutServer
from ..utils.api.request import L4API


async def draw_one_ip(host: str, port: int):
    """输出单个ip"""
    # 先用文字凑合
    try:
        ser_list = await L4API.a2s_info([(host, port)], is_player=True)
    except asyncio.exceptions.TimeoutError:
        return "服务器无响应"
    player_msg = ""
    one_server = ser_list[0][0]
    one_player = ser_list[0][1]

    if len(one_player):
        max_duration_len = max(
            [len(str(await convert_duration(i.duration))) for i in one_player],
        )
        max_score_len = max(len(str(i.score)) for i in one_player)

        for player in one_player:
            soc = "[{:>{}}]".format(player.score, max_score_len)
            chines_dur = await convert_duration(player.duration)
            dur = "{:^{}}".format(chines_dur, max_duration_len)
            name_leg = len(player.name)
            if name_leg > 2:
                # xing = "*" * (name_leg - 2)
                name = f"{player.name[0]}xing{player.name[-1]}"
            else:
                name = player.name
            player_msg += f"{soc} | {dur} | {name} \n"
    else:
        player_msg = "服务器感觉很安静啊"

    msg = f"""*{one_server.server_name}*
游戏: {one_server.folder}
地图: {one_server.map_name}
人数: {one_server.player_count}/{one_server.max_players}"""
    if one_server.ping is not None:
        msg += f"""
ping: {one_server.ping * 1000:.0f}ms
{player_msg}"""
    if config.l4_show_ip:
        msg += f"""
connect {host}:{port}"""
    return msg


async def get_much_server(server_json: List[NserverOut], command: str):
    out_server: List[OutServer] = []
    search_list: List[Tuple[str, int]] = []
    for i in server_json:
        search_list.append((i["host"], i["port"]))

    all_server = await L4API.a2s_info(search_list, is_player=True)

    for index, i in enumerate(all_server):
        out_server.append(
            {
                "server": i[0],
                "player": i[1],
                "host": server_json[index]["host"],
                "port": server_json[index]["port"],
                "command": command,
                "id_": server_json[index]["id"],
            },
        )

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
