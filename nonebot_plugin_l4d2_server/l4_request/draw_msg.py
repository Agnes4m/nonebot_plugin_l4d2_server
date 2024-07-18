import asyncio

from ..utils.api.request import L4API


async def draw_one_ip(host: str, port: int):
    """输出单个ip"""
    # 先用文字凑合
    try:
        one_server = await L4API.a2s_info(host, port)
        one_player = await L4API.a2s_players(host, port)
    except asyncio.exceptions.TimeoutError:
        return "服务器无响应"
    player_msg = ""

    max_duration_len = max([len(str(i.duration)) for i in one_player])
    max_score_len = max([len(str(i.score)) for i in one_player])

    for player in one_player:
        soc = "[{:>{}}]".format(player.score, max_score_len)
        chines_dur = await convert_duration(player.duration)
        dur = "{:^{}}".format(chines_dur, max_duration_len)

        player_msg += f"{soc} | {dur} | {player.name} \n"

    return f""" 【{one_server.server_name}】
游戏: {one_server.folder}
地图: {one_server.map_name}
ping: {one_server.ping*1000:.1f}ms
{player_msg}
connect: {host}:{port}
"""


async def convert_duration(duration: float) -> str:
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    time_str = ""
    if hours > 0:
        time_str += f"{int(hours)}h "
    if minutes > 0 or hours > 0:
        time_str += f"{int(minutes)}m "
    time_str += f"{int(seconds)}s"
    return time_str.strip()
