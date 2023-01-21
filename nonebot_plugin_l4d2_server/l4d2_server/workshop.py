import httpx
from nonebot.log import logger
try:
    import ujson as json
except:    
    import json

async def workshop_to_dict(msg:str):
    """把创意工坊的id，转化为信息字典"""
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
    i = data
    out['名字'] = i['title']
    out['游戏'] = i['app_name']
    out['下载地址'] = i['file_url']
    out['图片地址'] = i['preview_url']
    out['细节'] = i['file_description']
    return out
    
    
    

    