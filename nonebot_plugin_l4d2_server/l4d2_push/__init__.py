from pathlib import Path
import re
from typing import Dict,List,Union
try:
    import ujson as json
except:
    import json

from nonebot.log import logger
from nonebot import get_driver,on_command,get_bot
from nonebot import require
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import GroupMessageEvent,MessageSegment,Message
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from ..l4d2_utils.command import get_ip_to_mes
from ..l4d2_utils.utils import extract_last_digit
from ..l4d2_utils.config import l4_config

driver = get_driver()
sch_json = Path('data/L4D2/scheduler.json')
if not sch_json.exists():
    with sch_json.open('w') as f:
        json.dump({}, f ,ensure_ascii=False)
        
add_rss = on_command('add_rss',aliases={'求生定时添加'},priority= 30,permission= SUPERUSER| GROUP_ADMIN | GROUP_OWNER)
del_rss = on_command('del_rss',aliases={'求生定时删除'},priority= 30,permission= SUPERUSER| GROUP_ADMIN | GROUP_OWNER)

@add_rss.handle()
async def _(event:GroupMessageEvent , matcher:Matcher ,args: Message = CommandArg()):
    group_id = event.group_id
    msg = args.extract_plain_text()
    command,message = await extract_last_digit(msg)
    push_msg =  await get_ip_to_mes(msg= message,  command= command)
    if push_msg in ["服务器无响应" ,None] :
        await matcher.finish('无响应的服务器，请检查')
    else:
        return_msg = await add_or_update_data(group_id,msg)
        print(return_msg)
        if isinstance(push_msg , bytes):
            await matcher.send(MessageSegment.image(push_msg))
        else:
            await matcher.send(push_msg)
        if return_msg == 'add':
            await matcher.send(f'已添加群定时任务【{msg}】10次')
        elif return_msg in ['update','change']:
            await matcher.send(f'已更新群定时任务【{msg}】10次')

@del_rss.handle()
async def _(event:GroupMessageEvent , matcher:Matcher):
    group_id = event.group_id
    await add_or_update_data(group_id, '' , ad_mode= 'del')
    await matcher.finish('已删除群定时任务')



async def add_or_update_data(group_id:int, some_str :str = '',ad_mode :str = 'add'):
    """添加或者删除定时任务
    mode == [new,update,del,change]
    """
    group_id = str(group_id)
    sch_json = Path('data/L4D2/scheduler.json')
    if ad_mode == 'add':
        if sch_json.exists():
            with sch_json.open(encoding='utf-8') as f:
                scheduler_data = json.load(f)
            try:
                times , old_msg = scheduler_data[group_id]
                scheduler_data[group_id] = [l4_config.l4_push_times, some_str]
                if old_msg == some_str:
                    mode = 'update' 
                else:
                    mode = 'change'
            except:
                scheduler_data[group_id] = [l4_config.l4_push_times, some_str]
                mode = 'new'

        else:
            scheduler_data = {group_id: [l4_config.l4_push_times, some_str]}
            mode = 'new'
            
        with sch_json.open('w',encoding='utf-8') as f:
            json.dump(scheduler_data, f ,ensure_ascii=False)
    
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
            
        with sch_json.open('w',encoding='utf-8') as f:
            json.dump(scheduler_data, f ,ensure_ascii=False)  
            
    return mode

async def rss_ip():
    sch_json = Path('data/L4D2/scheduler.json')
    
    if sch_json.exists():
        with sch_json.open(encoding='utf-8') as f:
            scheduler_data:Dict[str,List[Union[int,str]]] = json.load(f)
            
            for key, value in scheduler_data.items():
                recipient_id = int(key)
                count = value[0]
                msg = value[-1]
                
                if count > 0:
                    await send_message(recipient_id, msg)
                    count -= 1
                
                scheduler_data[key][0] = count  # 更新次数
                
        with sch_json.open(mode='w',encoding='utf-8') as f:
            json.dump(scheduler_data, f ,ensure_ascii=False)
        
async def send_message(recipient_id :int, msg :str):
    # 执行发送消息的操作，参数可以根据需要进行传递和使用
    command,message = await extract_last_digit(msg)
    push_msg =  await get_ip_to_mes(msg= message,  command= command)
    if isinstance(push_msg ,bytes):
        await get_bot().send_group_msg(group_id=recipient_id, message=MessageSegment.image(push_msg))
    elif msg and isinstance(push_msg ,str):
        await get_bot().send_group_msg(group_id=recipient_id, message=push_msg)
    
@driver.on_bot_connect
async def _():    
    logger.success('已成功启动求生定时推送')
    scheduler.add_job(rss_ip, "interval", minutes=l4_config.l4_push_interval, id="rss_ip")
    