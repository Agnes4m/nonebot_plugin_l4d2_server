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
from nonebot.adapters.onebot.v11 import GroupMessageEvent,MessageSegment
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from ..l4d2_utils.command import get_ip_to_mes

driver = get_driver()
sch_json = Path('data/L4D2/scheduler.json')
add_rss = on_command('l4_rss',aliases={'求生添加定时'},priority= 30,permission= SUPERUSER| GROUP_ADMIN | GROUP_OWNER)
del_rss = on_command('l4_rss',aliases={'求生删除定时'},priority= 30,permission= SUPERUSER| GROUP_ADMIN | GROUP_OWNER)

@add_rss.handle()
async def _(event:GroupMessageEvent , matcher:Matcher ,msg: str = RawCommand()):
    group_id = event.group_id
    push_msg =  await get_ip_to_mes(msg)
    if push_msg == "服务器无响应":
        await matcher.finish(f'无响应的服务器，请检查')
    else:
        return_msg = await add_or_update_data(group_id,msg)
        if return_msg == 'add':
            await matcher.finish(f'已添加群定时任务【{msg}】10次')
        elif return_msg == 'update':
            await matcher.finish(f'已更新群定时任务【{msg}】10次')

@del_rss.handle()
async def _(msg:str , event:GroupMessageEvent , matcher:Matcher):
    group_id = event.group_id
    await add_or_update_data(group_id,msg , ad_mode= 'del')
    await matcher.finish(f'已删除群定时任务')



async def add_or_update_data(group_id, some_str :str = '',ad_mode :str = 'add'):
    """添加或者删除定时任务
    mode == [new,update,del,change]
    """
    sch_json = Path('data/L4D2/scheduler.json')
    if ad_mode == 'add':
        if sch_json.exists():
            with sch_json.open() as f:
                scheduler_data = json.load(f)
            try:
                times , old_msg = scheduler_data[group_id]
                scheduler_data[group_id] = [10, some_str]
                if old_msg == some_str:
                    mode = 'update' 
                else:
                    mode = 'change'
            except:
                scheduler_data[group_id] = [10, some_str]

        else:
            scheduler_data = {group_id: [10, some_str]}
            mode = 'new'
            
        with sch_json.open('w') as f:
            json.dump(scheduler_data, f)
    
    else:
        if sch_json.exists():
            with sch_json.open() as f:
                scheduler_data = json.load(f)
            try:
                times , old_msg = scheduler_data[group_id]  
                scheduler_data[group_id] = [0, old_msg]
            except:      
                scheduler_data[group_id] = [0, some_str]
        else:
            scheduler_data = {group_id: [0, some_str]}
        mode = 'del'
            
        with sch_json.open('w') as f:
            json.dump(scheduler_data, f)   
            
    return mode

async def rss_ip():
    sch_json = Path('data/L4D2/scheduler.json')
    
    if sch_json.exists():
        with sch_json.open(encoding='utf-8') as f:
            scheduler_data:Dict[int,List[Union[int,str]]] = json.load(f)
            
            for key, value in scheduler_data.items():
                recipient_id = key
                count = value[0]
                msg = value[-1]
                
                if count > 0:
                    await send_message(recipient_id, msg)
                    count -= 1
                
                scheduler_data[key][0] = count  # 更新次数
                
        with sch_json.open(mode='w',encoding='utf-8') as f:
            json.dump(scheduler_data, f)
        
async def send_message(recipient_id :int, msg :str):
    # 执行发送消息的操作，参数可以根据需要进行传递和使用
    push_msg =  await get_ip_to_mes(msg)
    if isinstance(msg ,bytes):
        await get_bot().send_group_msg(group_id=recipient_id, message=MessageSegment.image(push_msg))
    elif msg and isinstance(msg ,str):
        await get_bot().send_group_msg(group_id=recipient_id, message=msg)
    
    
    
scheduler.add_job(rss_ip, "cron", minute=3, id="rss_ip")
    