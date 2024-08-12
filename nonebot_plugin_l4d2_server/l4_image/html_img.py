import random
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
            print(sorted_players)
            server_info["player"] = sorted_players
        else:
            server_info["player"] = []

        # server_info["server"].server_type= f"{server_info['server'].server_type}.svg"
    print(server_dict)
    pic = await get_server_img(server_dict)
    if pic:
        logger.success("正在输出图片")
    else:
        logger.warning("我的图图呢")
    return pic


async def get_server_img(plugins: List[OutServer]) -> Optional[bytes]:
    try:
        if config.l4_style == "孤独摇滚":
            template = env.get_template("Bocchi_The_Rock.html")
        elif config.l4_style == "电玩像素":
            template = env.get_template("Pixel.html")
        elif config.l4_style == "缤纷彩虹":
            template = env.get_template("Rainbow.html")
        elif config.l4_style == "随机":
            html_files = [
                str(f.name) for f in template_path.rglob("*.html") if f.is_file()
            ]
            template = env.get_template(random.choice(html_files))
        else:
            template = env.get_template("normal.html")
        content = await template.render_async(
            plugins=plugins,
            max_count=config.l4_players,
        )
        return await html_to_pic(
            content,
            wait=0,
            viewport={"width": 100, "height": 100},
            template_path=f"file://{template_path.absolute()}",
        )
    except Exception as e:
        logger.warning(f"Error in get_help_img: {e}")
    return None


# async def server_group_ip_pic(msg_list: List[ServerGroup]) -> bytes:
#     """
#     输入一个群组字典列表,输出图片
#     msg_dict:folder/name/map_/players/max_players/Players/[Name]
#     """
#     template = env.get_template("group_ip.html")
#     html = await template.render_async(plugins=msg_list)
#     return await html_to_pic(
#         html=html,
#         wait=0,
#         viewport={"width": 1100, "height": 800},
#         template_path=f"file://{template_path.absolute()}",
#     )
