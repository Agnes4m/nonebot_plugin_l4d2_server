from .config import players_data
from nonebot.log import logger
from bs4 import BeautifulSoup
import httpx

def get_steamid(id:str):
    """如果是昵称则返回steamid"""
    if id.startswith('STEAM'):
        return id
    else:
        for key1,usr_id in players_data.items():
            for key2,value in usr_id.items():
                if value == id:
                    data = players_data[key1]['steam_id']

def read_player(id):
    """读取用户绑定信息dict"""
    for i in players_data:
        if id == i:
            player_data = players_data[id]
            logger.info(player_data)
            return player_data
    return ''   

def id_steam(id):
    """qq查steamid"""
    play_dict = read_player(id)
    name = play_dict['steam_id']
    return name

def id_name(id):
    """qq查名字"""
    play_dict = read_player(id)
    name = play_dict['usr_id']
    return name
        
def anne_search(name):
    """输入名字或者steamid返回列表["""
    url = 'https://sb.trygek.com/l4d_stats/ranking/search.php'
    data = {'search': name}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = httpx.post(url,data = data,headers=headers,timeout=60).content.decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    # 获取标题
    title = []
    thead = soup.find('thead')
    for i in thead.find_all('td'):
        tag = i.text.strip()
        title.append(tag)
    title.append('steamid')
    # 角色信息
    datas = soup.find('table')
    datas = datas.find('tbody')
    datas = datas.find_all('tr')
    return [datas,title]

def name_steamid_html(name):
    """您称通过网页来返回求生steamid"""
    data_title = anne_search(name)
    data = data_title[0]
    for i in data:
        onclick:str = i['onclick']
        steamid = onclick.split('=')[2].strip("'")
        return steamid