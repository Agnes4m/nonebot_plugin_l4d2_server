from nonebot_plugin_htmlrender import html_to_pic
from ..config import TEXT_PATH
from .download import get_head_by_user_id_and_save
from .send_image_tool import convert_img
from bs4 import BeautifulSoup
from nonebot.log import logger
from jinja2 import Environment, FileSystemLoader

async def out_png(usr_id,data_dict:dict):
    """使用html来生成图片"""
    template_path = TEXT_PATH/"template"
    logger.info(template_path)
    with open((template_path/"anne.html"),"r", encoding="utf-8") as file:
        data_html = file.read()
    # content = template.render_async()
    soup = BeautifulSoup(data_html, 'html.parser')
    new_html = await dict_to_html(usr_id,data_dict,soup)
    pic = await html_to_pic(
                new_html,
                wait=0,
                viewport={"width": 1100, "height": 800},
                template_path=f"file://{template_path.absolute()}",)
    print(type(pic))
    return pic


async def dict_to_html(usr_id,DETAIL_MAP:dict,soup:BeautifulSoup):
    """输入qq、字典，获取新的html"""
    DETAIL_right = {}
    DETAIL_right['name'] = DETAIL_MAP['Steam 名字:']
    DETAIL_right['Steam_ID'] = DETAIL_MAP['Steam ID:']
    DETAIL_right['play_time'] = DETAIL_MAP['游玩时间:']
    DETAIL_right['last_online'] = DETAIL_MAP['最后上线:']
    DETAIL_right['rank'] = DETAIL_MAP['排行:']
    DETAIL_right['points'] = DETAIL_MAP['分数:']
    DETAIL_right['point_min'] = DETAIL_MAP['每分钟获取分数:']
    DETAIL_right['killed'] = DETAIL_MAP['感染者消灭:']
    DETAIL_right['shut'] = DETAIL_MAP['爆头:']        
    DETAIL_right['out'] = DETAIL_MAP['爆头率:']
    DETAIL_right['playtimes'] = DETAIL_MAP['游玩地图数量:']
    logger.info(DETAIL_right)
    html_text = soup.prettify()
    for key, value in DETAIL_right.items():
        html_text = html_text.replace(key,value)
    # 头像
    temp = await get_head_by_user_id_and_save(usr_id)
    res = await convert_img(temp,is_base64=True)
    finna_html = html_text.replace("player.jpg",f"data:image/png;base64,{res}")
    return finna_html
    
async def server_ip_pic(msg_dict:list[dict]):
    """
    输入一个字典列表，输出图片
    msg_dict:folder/name/map_/players/max_players/Players/[Name]
    """
    for one in msg_dict:
        one['max_players'] = one['players'] + '/' + one['max_players']
    
    template_path = TEXT_PATH/"template"
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template('ip.html')
    html = template.render(data = msg_dict)
    pic = await html_to_pic(
            html,
            wait=0,
            viewport={"width": 1080, "height": 400},
            template_path=f"file://{template_path.absolute()}",)
    return pic

