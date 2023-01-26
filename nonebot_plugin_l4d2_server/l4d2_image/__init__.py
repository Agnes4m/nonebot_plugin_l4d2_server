from nonebot_plugin_htmlrender import html_to_pic
from ..config import TEXT_PATH
try:
    from .download import get_head_steam_and_save
except:
    from .download import get_head_by_user_id_and_save
from .send_image_tool import convert_img
from bs4 import BeautifulSoup
from nonebot.log import logger
from jinja2 import Environment, FileSystemLoader

async def out_png(usr_id,data_dict:dict):
    """使用html来生成图片"""
    template_path = TEXT_PATH/"template"
    with open((template_path/"anne.html"),"r", encoding="utf-8") as file:
        data_html = file.read()
    # content = template.render_async()
    soup = BeautifulSoup(data_html, 'html.parser')
    new_html = await dict_to_html(usr_id,data_dict,soup)
    
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template('anne.html')
    html = template.render(data = new_html)
    
    pic = await html_to_pic(
                html,
                wait=0,
                viewport={"width": 1100, "height": 800},
                template_path=f"file://{template_path.absolute()}",)
    print(type(pic))
    return pic


async def dict_to_html(usr_id,DETAIL_MAP:dict,soup:BeautifulSoup):
    """输入qq、字典，获取新的msg替换html"""
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
    DETAIL_right['url'] = DETAIL_MAP['个人资料']
    DETAIL_right['one_msg'] = DETAIL_MAP['一言']
    # html_text = soup.prettify()
    # for key, value in DETAIL_right.items():
    #     html_text = html_text.replace(key,value)
    # 头像
    temp = await get_head_by_user_id_and_save(usr_id)
    # temp = await get_head_steam_and_save(usr_id,DETAIL_right['url'])
    res = await convert_img(temp,is_base64=True)
    DETAIL_right['header'] = f"data:image/png;base64,{res}"
    data_list = [DETAIL_right]
    return data_list
    
async def server_ip_pic(msg_dict:list[dict]):
    """
    输入一个字典列表，输出图片
    msg_dict:folder/name/map_/players/max_players/Players/[Name]
    """
    for one in msg_dict:
        one['max_players'] = one['players'] + '/' + one['max_players']
        players_list = []
        try:
            for one_player in one['Players']:
                player_str = one_player['Name'] +' | ' + one_player['Duration']
                players_list.append(player_str)
            one['Players'] = players_list
    # one['Players'] = one['Players']['Name'] + one['Players']['Dutation']
        except KeyError:
            continue
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

