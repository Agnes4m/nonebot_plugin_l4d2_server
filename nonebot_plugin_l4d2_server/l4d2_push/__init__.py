from pathlib import Path
from typing import Dict,List,Union
try:
    import ujson
except:
    import json

from nonebot import get_driver,on_command,get_bot
from nonebot import require
from nonebot.permission import SUPERUSER
from nonebot.params import RawCommand
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from ..l4d2_utils.command import get_ip_to_mes

driver = get_driver()
sch_json = Path('data/L4D2/scheduler.json')
rss = on_command('l4_rss',aliases={'求生定时'},priority= 30,permission= SUPERUSER| GROUP_ADMIN | GROUP_OWNER)

@rss.handle()
async def _(msg:str , event:GroupMessageEvent , matcher:Matcher ,command: str = RawCommand()):
    group_id = event.group_id
    await add_or_update_data(group_id,command)

async def add_or_update_data(group_id, some_str):
    sch_json = Path('data/L4D2/scheduler.json')
    
    if sch_json.exists():
        with sch_json.open() as f:
            scheduler_data = json.load(f)
        
        scheduler_data[group_id] = [12, some_str]  # 添加或更新数据
        
        with sch_json.open('w') as f:
            json.dump(scheduler_data, f)
    else:
        scheduler_data = {group_id: [12, some_str]}  # 创建新的数据字典
        
        with sch_json.open('w') as f:
            json.dump(scheduler_data, f)

async def rss_ip():
    sch_json = Path('data/L4D2/scheduler.json')
    
    if sch_json.exists():
        with sch_json.open(encoding='utf-8') as f:
            scheduler_data:Dict[int,List[Union[int,str]]] = json.load(f)
            
            for key, value in scheduler_data.items():
                recipient_id = key
                count = value[0]
                msg = value[-1]  # 获取除次数外的其他参数
                
                if count > 0:  # 当次数大于0时执行操作
                    await send_message(recipient_id, msg)
                    count -= 1
                
                scheduler_data[key][0] = count  # 更新次数
                
        with sch_json.open(mode='w',encoding='utf-8') as f:
            json.dump(scheduler_data, f)
        
async def send_message(recipient_id, msg):
    # 执行发送消息的操作，参数可以根据需要进行传递和使用
    await get_bot().send_group_msg(group_id=recipient_id, message=msg)
    
    
scheduler.add_job(rss_ip, "cron", minute=5, id="rss_ip")
    