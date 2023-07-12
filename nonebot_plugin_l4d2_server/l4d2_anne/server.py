import httpx
from bs4 import BeautifulSoup
import json
import asyncio
from typing import Dict, List
from pathlib import Path

from ..l4d2_utils.config import CONFIG_PATH, anne_url, ANNE_IP, headers

from ..l4d2_queries.ohter import ALL_HOST

# 储存anne服务器ip
anne_url = "https://sb.trygek.com/"
ANNE_IP = {}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"
}


async def updata_anne_server():
    """更新anne服务器列表"""
    data = httpx.get(anne_url, headers=headers).content
    soup = BeautifulSoup(data, "html.parser")
    tbody = soup.find("tbody")
    if not tbody:
        return
    n = 0
    ip_list = []
    while n < 50:
        n += 1
        tr = tbody.find(id=f"server_{n}")  # type: ignore
        if tr:
            td: str = tr.select_one("td:nth-of-type(5)").get_text()  # type: ignore
        else:
            continue
        if not td:
            continue
        else:
            ip_list.append(td)
    if not ip_list:
        return None
    ip_dict: Dict[str, List[str]] = {}
    ip_new_list: List[Dict[str, str]] = []
    n: int = 0
    for i in ip_list:
        n += 1
        ip_new_list.append({"id": str(n), "ip": i})
    ip_dict = {"云": [d["ip"] for d in ip_new_list]}
    ANNE_IP.update(ip_dict)
    with open(Path(CONFIG_PATH.parent / "l4d2/云.json"), "w", encoding="utf-8") as f:
        json.dump(ANNE_IP, f, indent=4, ensure_ascii=False)
    print(ANNE_IP)
    return ANNE_IP


asyncio.run(updata_anne_server())


def server_key():
    """响应的服务器开头"""
    a = set()
    try:
        for tag1, value in ALL_HOST.items():
            a.add(tag1)
    except AttributeError:
        a.add("希腊那我从来没有想过这个事情")
    return a
