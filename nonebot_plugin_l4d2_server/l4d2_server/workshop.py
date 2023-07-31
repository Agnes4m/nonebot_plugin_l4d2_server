from typing import Dict, List, Union

import httpx

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


async def api_get_json(msg: str) -> Dict[str, str]:
    url_serach = "https://db.steamworkshopdownloader.io/prod/api/details/file"
    data: Dict[str, str] = {msg: ""}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url_serach, headers=headers, data=data)
        data_msg = response.content.decode("utf-8")
        datas: Dict[str, str] = json.loads(data_msg[1:-1])
        return datas


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
