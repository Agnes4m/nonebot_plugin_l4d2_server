import asyncio
import json
from typing import Dict, List

import aiohttp


# from ..l4d2_image.steam import url_to_msg
async def url_to_msg(url: str):
    """获取URL数据的字节流"""

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=600) as response:
            if response.status == 200:
                return await response.text()
            return None


async def get_himi_ip():
    url = "http://xg-squ.himeneko.cn:8080/cq/servers?nonce=272526ut&token=07163dc62723159a6accfc1fcad2029b"
    msg = await url_to_msg(url)
    if msg:
        msg_json: Dict[str, List[Dict[str, str]]] = json.loads(msg)
    else:
        return
    msg_list = msg_json["list"]
    new_json: Dict[str, List[Dict[str, str]]] = {}
    for one_server in msg_list:
        new_server: Dict[str, str] = {}
        tag = await name_to_tag(one_server["name"])
        new_server["id"] = await name_to_id(
            one_server["name"],
            tag,
            new_json,
        )
        new_server["ip"] = one_server["url"]
        print(tag, "|", new_server["id"])
        if tag in new_json:
            new_json[tag].append(new_server)
        else:
            new_json[tag] = [new_server]


async def name_to_tag(name: str):
    """获取tag"""
    while name and ord(name[0]) == 65279:
        name = name[1::]
    if name.startswith("["):
        tag = name[1::].split("]")[0].split(" ")[0]
        # print(tag, "|", name)
    elif name.startswith("【"):
        tag = name[1::].split("】")[0].split(" ")[0]
    elif "电信云服" in name:
        tag = "云"
    elif "Neko" in name:
        tag = "Neko"
    else:
        tag = name[0]

    return tag


async def name_to_id(name: str, tag: str, msg_dict: Dict[str, List[Dict[str, str]]]):
    while name and ord(name[0]) == 65279:
        name = name[1::]
    if "#" in name:
        index = name.find("#")
        number = ""
        for i in range(index + 1, len(name)):
            if name[i].isdigit():
                number += name[i]
                if len(number) == 2:  # 只提取一个或两个数字
                    return str(number)
            else:
                break
    elif "[服]" in name:
        index = name.find("[服]")
        number = ""
        for i in range(index - 1, -1, -1):
            if name[i].isdigit():
                number = name[i] + number
                if len(number) == 1:  # 只提取一个数字
                    return str(number)
            else:
                break
    id_list: List[str] = []
    try:
        for one_server in msg_dict[tag]:
            id_list.append(str(one_server["id"]))
        for one in range(1, 100):
            if str(one) not in id_list:
                return str(one)
    except KeyError:
        return "1"
    return "1"


if __name__ == "__main__":
    asyncio.run(get_himi_ip())
