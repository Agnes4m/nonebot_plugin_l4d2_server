import requests
from nonebot.log import logger
from pathlib import Path
from bs4 import BeautifulSoup
from .config import l4_steamid,players_data
try:
    import ujson as json
except:
    import json

def anne_search(name):
    """输入名字或者steamid返回文字信息"""
    url = 'https://sb.trygek.com/l4d_stats/ranking/search.php'
    data = {'search': name}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = requests.post(url,data = data,headers=headers).content.decode('utf-8')
    return anne_html(data)

def anne_local(name):
    """输入名字或者steamid返回本地缓存信息(未完成)"""
    with open('ser.txt','r', encoding= 'utf-8') as f:
        data = f.read()

def anne_html(data):
    """从html里提取玩家信息，多出一行"""
    soup = BeautifulSoup(data, 'html.parser')
    # 获取标题
    title = []
    thead = soup.find('thead')
    for i in thead.find_all('td'):
        tag = i.text.strip()
        title.append(tag)
    title.append('steamid')
    # 角色信息
    data = soup.find('table')
    data = data.find('tbody')
    data = data.find_all('tr')
    logger.info(data)
    if data[0] == "No Player found.":
        return '搜不到该玩家...\n'
    data_list = []
    for i in data:
        Rank = i.find('td', {'data-title': 'Rank:'}).text.strip()
        player = i.find('td', {'data-title': 'Player:'}).text.strip()
        points = i.find('td', {'data-title': 'Points:'}).text.strip()
        country = i.find('img')['alt']
        playtime = i.find('td', {'data-title': 'Playtime:'}).text.strip()
        last_online = i.find('td', {'data-title': 'Last Online:'}).text.strip()
        onclick = i['onclick']
        steamid = onclick.split('=')[2].strip("'")
        play_json ={
            title[0]:Rank,
            title[1]:player,
            title[2]:points,
            title[3]:country,
            title[4]:playtime,
            title[5]:last_online,
            title[6]:steamid
        }
        data_list.append(play_json)

    # 列表转输出文字
    mes = '搜索到以下玩家信息'
    for one in data_list:
        if l4_steamid:
            x = 7
        else:
            x = 6
        for i in range(x):
            mes += '\n' + str(title[i]) + ':' + str(one[title[i]])
        mes += '\n--------------------'    
    return mes

def read_player(id):
    """读取用户绑定信息"""
    for i in players_data:
        if id == i:
            player_data = players_data[id]
            logger.info(players_data)
            logger.info(player_data)
            return player_data
    return ''     
   
def write_player(id,msg:str,nickname:str):
    """绑定用户qq"""
    play_dict = read_player(id)
    # 判断是steam
    if msg.startswith('STEAM'):
        if not play_dict:
            new_dict = {"steam_id":msg}
        else :
            try:
                a = play_dict["steam_id"]
                mes = '您已经绑定过了steamid,绑定信息是 '+ a
                return mes
            except KeyError:
                new_dict = {"steam_id":msg}
            try:
                b = play_dict["usr_id"]
                new_dict = dict(play_dict, **new_dict)
            except KeyError:
                new_dict = {"steam_id":msg}
        logger.info(new_dict)
        add_player(id,new_dict)
        mes = '绑定成功喵~\nQQ:' + nickname +'\n' + 'steamid:'+msg
        return mes
    else:
        if not play_dict:
            new_dict = {"usr_id":msg}
        else :
            try:
                a = play_dict["usr_id"]
                mes = '您已经绑定过了昵称,昵称是 '+ a
                return mes
            except KeyError:
                new_dict = {"steam_id":msg}
            try:
                b = play_dict["usr_id"]
                new_dict = dict(play_dict, **new_dict)
            except KeyError:
                new_dict = {"usr_id":msg}
        logger.info(new_dict)
        add_player(id,new_dict)
        mes = '绑定成功喵~\nQQ:' + nickname +'\n' + 'steam昵称:'+msg
        return mes

        
def add_player(id:str,new_dict:dict):
    """写入绑定信息"""
    axis = {id:new_dict}
    logger.info(axis)
    players_data.update(axis)
    with open(Path(__file__).parent.joinpath('data/player.json'), "w", encoding="utf8") as new:
        json.dump(players_data, new, ensure_ascii=False, indent=4)
        
def del_player(id:str):
    """删除绑定信息,返回消息"""
    try:
        del players_data[str(id)]
        with open(Path(__file__).parent.joinpath('data/player.json'), "w", encoding="utf8") as new:
            json.dump(players_data, new, ensure_ascii=False, indent=4)
        return '删除成功喵~'
    except KeyError:
        return '你还没有绑定过，请使用[求生绑定+昵称/steamid]'

    
def id_to_mes(name,usr_id):
    """根据name从json查找,返回昵称或者steamid"""
    start = name.find("[CQ:at,qq=")
    if start == 1:
        end = name.find("]", start)
        usr_id = name[start:end+1]
    if len(name)== 0:
        for i in players_data:
            i = str (i)
            usr_id = str(usr_id)
            if usr_id == i:
                data = players_data[i]
                try:
                    name = data["steam_id"]
                except KeyError:
                    try:
                        name = data["usr_id"]
                    except KeyError:
                        mes = '绑定信息不存在，请使用[求生绑定+昵称/steamid]'
                        return ''
    logger.info(name)
    return name