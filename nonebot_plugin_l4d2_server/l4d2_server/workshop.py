import httpx
from nonebot.log import logger
try:
    import ujson as json
except:    
    import json

async def workshop_to_dict(msg:str):
    """把创意工坊的id，转化为信息字典"""
    i = await api_get_json(msg)
    
    # 处理是否是多地图文件
    if i['file_url'] == i['preview_url']:
        return await primary_map(i)
    else:
        return await only_map(i)

    
async def api_get_json(msg:str) ->dict:
    url_serach = 'https://db.steamworkshopdownloader.io/prod/api/details/file'
    data = f'[{msg}]'
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    }
    data = httpx.post(url=url_serach,headers= headers,data=data).content.decode('utf-8')
    logger.info(data)
    out = {}
    data = data[1:-1]
    data = json.loads(data)
    return data
    

async def only_map(i:dict):
    """单地图下载"""
    out = {}
    out['名字'] = i['title']
    out['游戏'] = i['app_name']
    out['下载地址'] = i['file_url']
    out['图片地址'] = i['preview_url']
    out['细节'] = i['file_description']
    return out

async def primary_map(i):
    """主地图返回多地图参数"""
    map_list = []
    map_list.append(i)
    for one in i['children']:
        map_list.append(await api_get_json(one['publishedfileid']))
    return map_list

