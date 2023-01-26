import httpx
from bs4 import BeautifulSoup
import json
from pathlib import Path
from ..config import TEXT_PATH,anne_url

# 储存anne服务器ip
ANNE_IP:dict = json.load(open(Path(__file__).parent.parent.joinpath(
        'data/L4D2/server.json'), "r", encoding="utf8"))


async def updata_anne_server():
    """更新anne服务器列表"""
    data = httpx.get(anne_url).content
    soup = BeautifulSoup(data, 'html.parser')
    tbody = soup.find('tbody')
    n = 0
    ip_list=[]
    while n < 50:
        n += 1
        tr = tbody.find(id = f'server_{n}')
        if tr:
            td = tr.select_one("td:nth-of-type(5)").get_text()
        else:
            continue
        if td:
            ip_list.append(td)
    if not ip_list:
        return None
    ip_dict = {}
    n = 0
    for i in ip_list:
        n += 1
        ip_dict.update({f'云{n}':ip_list[n-1]})
    ANNE_IP.update(ip_dict)
    with open(Path(TEXT_PATH.parent/'server.json'),'w',encoding='utf-8') as f:
        json.dump(ANNE_IP, f, indent=4, ensure_ascii=False)
    return ANNE_IP

async def read_anne_ip():
    """获取缓存ip"""
    with open(TEXT_PATH.parent/'server.json','r','utf-8') as f:
        data = json.load(f)
        return data
    
async def get_anne_ip(text: str) -> str:
    """从字典里返还消息, 抄(借鉴)的zhenxun-bot"""
    keys = ANNE_IP.keys()
    for key in keys:
        if text == key:
            return ANNE_IP[key]