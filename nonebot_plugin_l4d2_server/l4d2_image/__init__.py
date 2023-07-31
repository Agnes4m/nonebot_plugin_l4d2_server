from typing import List, Optional

import jinja2
from nonebot.log import logger
from nonebot_plugin_htmlrender import html_to_pic

# from .htmlimg import dict_to_dict_img
# from ..l4d2_anne.anne_telecom import ANNE_API
from ..l4d2_utils.config import TEXT_PATH, l4_config
from .download import get_head_by_user_id_and_save
from .send_image_tool import convert_img

template_path = TEXT_PATH / "template"

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path),
    enable_async=True,
)


async def out_png(usr_id, data_dict: dict):
    """使用html来生成图片"""
    # content = template.render_async()
    msg_dict = await dict_to_html(usr_id, data_dict)
    template = env.get_template("anne.html")
    html = await template.render_async(data=msg_dict)
    return await html_to_pic(
        html,
        wait=0,
        viewport={"width": 1100, "height": 800},
        template_path=f"file://{template_path.absolute()}",
    )


async def dict_to_html(usr_id, detail_map: dict):
    """输入qq、字典，获取新的msg替换html"""
    detail_right = {}
    detail_right["name"] = detail_map["Steam 名字:"]
    detail_right["Steam_ID"] = detail_map["Steam ID:"]
    detail_right["play_time"] = detail_map["游玩时间:"]
    detail_right["last_online"] = detail_map["最后上线:"]
    detail_right["rank"] = detail_map["排行:"]
    detail_right["points"] = detail_map["分数:"]
    detail_right["point_min"] = detail_map["每分钟获取分数:"]
    detail_right["killed"] = detail_map["感染者消灭:"]
    detail_right["shut"] = detail_map["爆头:"]
    detail_right["out"] = detail_map["爆头率:"]
    detail_right["playtimes"] = detail_map["游玩地图数量:"]
    detail_right["url"] = detail_map["个人资料"]
    detail_right["one_msg"] = detail_map["一言"]
    detail_right["last_one"] = detail_map["救援关"]
    # html_text = soup.prettify()
    # for key, value in detail_right.items():
    #     html_text = html_text.replace(key,value)
    # 头像
    temp = await get_head_by_user_id_and_save(usr_id)
    # temp = await get_head_steam_and_save(usr_id,detail_right['url'])
    if not temp:
        return None
    res = await convert_img(temp, is_base64=True)
    detail_right["header"] = f"data:image/png;base64,{res}"
    data_list: List[dict] = [detail_right]
    return data_list


async def server_ip_pic(msg_list: List[dict]):
    """
    输入一个字典列表，输出图片
    msg_dict:folder/name/map_/players/max_players/Players/[Name]
    """
    for server_info in msg_list:
        server_info[
            "max_players"
        ] = f"{server_info['players']}/{server_info['max_players']}"
        players_list = []
        if "Players" in server_info:
            sorted_players = sorted(
                server_info["Players"],
                key=lambda x: x.get("Score", 0),
                reverse=True,
            )[:4]
            for player_info in sorted_players:
                player_str = f"{player_info['name']} | {player_info['Duration']}"
                players_list.append(player_str)
            while len(players_list) < 4:
                players_list.append("")
            server_info["Players"] = players_list
    pic = await get_help_img(msg_list)
    if pic:
        logger.success("正在输出图片")
    else:
        logger.warning("我的图图呢")
    return pic


async def get_help_img(plugins: List[dict]) -> Optional[bytes]:
    try:
        if l4_config.l4_style == "black":
            template = env.get_template("help_dack.html")
        else:
            template = env.get_template("help.html")
        content = await template.render_async(plugins=plugins)
        return await html_to_pic(
            content,
            wait=0,
            viewport={"width": 100, "height": 100},
            template_path=f"file://{template_path.absolute()}",
        )
    except Exception as e:
        logger.warning(f"Error in get_help_img: {e}")
        return None
