import httpx
from typing import List

async def seach_map(msg:str,qq:str,key:str,mode:str = 'zh'):
    url = "http://106.13.207.45:4015/l4d2"
    json = {
        "mode":mode,
        "map_name":msg,
        "qq":qq,
        "key":key
    }
    print(json)
    file = httpx.post(url,json=json)
    if mode == 'zh':
        if file.status_code == 200:
            return file.json()
        elif file.status_code == 204:
            return "没有结果"
        elif file.status_code == 406:
            return "参数错误"
        elif file.status_code == 401:
            return file.json()
    elif mode == 'ip':
        return file.json()
    elif mode == 'first':
        ip_tag:list = file.json()
        return ip_tag
        

async def map_dict_to_str(data:List[dict]):
    msg = ""
    for key,value in data[0].items():
        if key == "url":
            continue
        msg += f"{key}:{value}\n"
    return msg

