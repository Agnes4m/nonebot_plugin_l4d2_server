import requests
from .utils import solve
from bs4 import BeautifulSoup
from .config import l4_steamid

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
    """从html里提取玩家信息"""
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
    mes = solve(mes)

    return mes