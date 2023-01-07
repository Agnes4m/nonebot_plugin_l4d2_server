
from nonebot.log import logger
from pathlib import Path

from .config import l4_steamid,players_data
from .seach import *
try:
    import ujson as json
except:
    import json


def anne_local(name):
    """输入名字或者steamid返回本地缓存信息(未完成)"""
    with open('ser.txt','r', encoding= 'utf-8') as f:
        data = f.read()

def anne_html(name):
    """从html里提取玩家信息，多出一行"""
    data_title = anne_search(name)
    data = data_title[0]
    title = data_title[1]
    if len(data) ==0 or data[0] == "No Player found.":
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

    
def id_to_mes(name,usr_id,at:list):
    """根据name从json查找,返回昵称或者steamid"""
    if at and at[0] != usr_id:
        at = at[0]
        usr_id = at
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
                        return mes
    logger.info(name)
    return name

def anne_rank(name:str):
    """用steamid,查详情,输出可以发送的信息"""
    if not name.startswith('STEAM'):
        name = name_steamid_html(name)
    data_dict = {}
    url ='https://sb.trygek.com/l4d_stats/ranking/player.php?steamid=' + name
    logger.info(url)
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    }
    data = httpx.get(url,headers=headers,timeout=30).content.decode('utf-8')
    data = BeautifulSoup(data, 'html.parser')
    detail = data.find_all('table')
    n = 0
    while n < 2:
        mes = ''
        detail2 = detail[n]
        tr = detail2.find_all('tr')
        for i in tr:
            title = i.find('td', {'class': 'w-50'})
            value = title.find_next_sibling('td')
            new_dict = {title.text:value.text}
            data_dict.update(new_dict)
        # print(data_dict)
        for i in data_dict:
            mes +='\n'+ i + data_dict[i]
        mes += '\n--------------------'
        n += 1
    logger.info(mes)
    return mes

        
