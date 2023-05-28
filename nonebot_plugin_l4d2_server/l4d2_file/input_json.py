from nonebot import on_fullmatch,on_notice
from nonebot.adapters.onebot.v11 import GroupMessageEvent,Message,NoticeEvent
import nonebot
from pathlib import Path
import httpx
try:
    import ujson as json
except:
    import json


upload = on_notice()
@upload.handle()
async def _(event:NoticeEvent):
    try:
        arg = event.dict()
        files:dict = arg['file']
        name:str = files['name']
        if arg['notice_type'] == 'offline_file' and name.endswith('.json'):
            jsons = json.loads(httpx.get(files['url']).content.decode('utf-8'))
            print(jsons)
            key = await up_date(jsons,name)
            if key:
                msg ='输入成功\n'
                for key, value in jsons.items():
                    msg += f"当前你的{key}指令：{len(value)}个\n"
                await upload.send(msg)
    except KeyError:
        pass
    
    

async def up_date(data, name):
    directory = Path("data/L4D2/l4d2")
    directory.mkdir(parents=True, exist_ok=True)
    
    file_path = directory / name
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)
    
    return True