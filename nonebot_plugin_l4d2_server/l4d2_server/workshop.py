from typing import Dict, List, Union

import httpx
from nonebot.log import logger

try:
    import ujson as json
except ImportError:
    import json


async def workshop_to_dict(msg: str):
    """把创意工坊的id，转化为信息字典"""
    i = await api_get_json(msg)

    # 处理是否是多地图文件
    if i["file_url"] == i["preview_url"]:
        return await primary_map(i)  # type: ignore
    return await only_map(i)


async def api_get_json(msg: str):
    url_search = "https://db.steamworkshopdownloader.io/prod/api/details/file"
    # data = {msg: ""}
    data = [int(msg)]
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://steamworkshopdownloader.io",
        "Referer": "https://steamworkshopdownloader.io/",
        "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url_search, headers=headers, json=data)
        data_msg = response.content.decode("utf-8", errors="ignore")
        logger.info(response.status_code)
        logger.info(data_msg)
        return json.loads(data_msg[1:-1])


async def only_map(i: Dict[str, str]):
    """单地图下载"""
    out: Dict[str, str] = {}
    out["名字"] = i["title"]
    out["游戏"] = i["app_name"]
    out["下载地址"] = i["file_url"]
    out["图片地址"] = i["preview_url"]
    out["细节"] = i["file_description"]
    return out


async def primary_map(i: Dict[str, List[Dict[str, str]]]):
    """主地图返回多地图参数"""
    map_list: List[Union[Dict[str, List[Dict[str, str]]], Dict[str, str]]] = []
    map_list.append(i)
    for one in i["children"]:
        map_list.append(await api_get_json(one["publishedfileid"]))
    return map_list


async def workshop_msg(msg: str):
    """url变成id，拼接post请求"""
    if msg.startswith("https://steamcommunity.com/sharedfiles/filedetails/?id"):
        if "&" in msg:
            msg = msg.split("&")[0]
        else:
            pass
        msg = msg.replace("https://steamcommunity.com/sharedfiles/filedetails/?id=", "")
    if msg.isdigit():
        data: Union[dict, List[dict]] = await workshop_to_dict(msg)
        return data
    return None
    return None
    return None
