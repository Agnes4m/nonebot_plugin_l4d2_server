from pathlib import Path
from typing import List, Optional

import jinja2
from nonebot.log import logger
from nonebot_plugin_htmlrender import html_to_pic

from ..config import config
from ..utils.api.models import OutServer

# from .htmlimg import dict_to_dict_img
# from ..l4d2_anne.anne_telecom import ANNE_API

template_path = Path(__file__).parent / "img/template"

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path),
    enable_async=True,
    autoescape=True,
)


async def server_ip_pic(server_dict: List[OutServer]):
    """
    输入一个字典列表,输出图片
    msg_dict:folder/name/map_/players/max_players/Players/[Name]
    """
    for server_info in server_dict:
        server_info["server"].player_count = (
            0
            if server_info["server"].player_count is None
            else server_info["server"].player_count
        )
        server_info["server"].max_players = (
            0
            if server_info["server"].max_players is None
            else server_info["server"].max_players
        )

        max_number = config.l4_players
        if server_info.get("player"):
            sorted_players = sorted(
                server_info["player"],
                key=lambda x: x.score,
                reverse=True,
            )[:max_number]
            logger.debug(sorted_players)

            # 时间转换
            max_duration_len = max(
                [len(str(await convert_duration(i.duration))) for i in sorted_players],
            )
            for player in sorted_players:
                chines_dur = await convert_duration(player.duration)
                dur = "{:^{}}".format(chines_dur, max_duration_len)
                player.name = str(player.name) + " | " + dur

            server_info["player"] = sorted_players
        else:
            server_info["player"] = []

    pic = await get_server_img(server_dict)
    if pic:
        logger.success("正在输出图片")
    else:
        logger.warning("我的图图呢")
    return pic


async def get_server_img(plugins: List[OutServer]) -> Optional[bytes]:
    try:
        if config.l4_style == "default":

            template = env.get_template("normal.html")
        else:
            template = env.get_template("normal_old.html")
        content = await template.render_async(
            servers=plugins,
            max_count=config.l4_players,
        )
        # with open("test.html", "w", encoding="utf-8") as f:
        #     f.write(content)
        return await html_to_pic(
            content,
            wait=0,
            viewport={"width": 100, "height": 100},
            template_path=f"file://{template_path.absolute()}",
        )
    except Exception as e:
        logger.warning(f"Error in get_server_img: {e}")
        return None


async def convert_duration(duration: float) -> str:
    """将秒数转换为易读的时间字符串格式（例如 '1h 30m 15s'）

    参数:
        duration: 秒数

    返回:
        格式化的时间字符串
    """
    total_seconds = int(duration)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    time_str = ""
    if hours > 0:
        time_str += f"{hours}h "
    if minutes > 0:
        time_str += f"{minutes}m "
    time_str += f"{seconds}s"
    return time_str
