import re
import asyncio
from typing import Type
from time import sleep

from nonebot import on_notice,on_command,on_regex,on_keyword,MatcherGroup
from nonebot.params import CommandArg,RawCommand,CommandStart
from nonebot.matcher import Matcher
import nonebot
from nonebot.adapters.onebot.v11 import (
    GroupUploadNoticeEvent,
    NoticeEvent,
    MessageEvent,
    Message,
    MessageSegment,
    GroupMessageEvent,
    )

from .l4d2_anne.server import server_key,ANNE_IP
from .config import *
from .l4d2_queries.qqgroup import split_maohao
# from .utils import qq_ip_queries_pic,json_server_to_tag_dict,get_anne_server_ip,get_tan_jian
from .utils import *
help_ = on_command('l4_help',aliases={'求生帮助'},priority=20,block=True)

# 服务器
# last_operation_time = nonebot.Config.parse_obj(nonebot.get_driver().config.dict()).SUPERUSERS



def wenjian(
event:NoticeEvent):
    args = event.dict()
    try:
        name: str = args['file']['name']
        usr_id = str(args['user_id'])
    except KeyError:
        return False
    if args['notice_type'] == 'offline_file':
        if l4_config.l4_master:
            return name.endswith(file_format) and usr_id in l4_config.l4_master
        else:
            return name.endswith(file_format)
    elif args['notice_type'] == 'group_upload':
        if l4_config.l4_master:
            return usr_id in l4_config.l4_master and name.endswith(file_format)
        else:
            return False

up = on_notice(rule=wenjian)



rename_vpk = on_regex(
        r"^求生地图\s*(\S+.*?)\s*(改|改名)?\s*(\S+.*?)\s*$",
    flags=  re.S,
    block= True,
    priority= 20,
    permission= Master,
)

find_vpk = on_command("l4_map",aliases={"求生地图","查看求生地图"},priority=25,block=True)
del_vpk = on_command("l4_del_map",aliases={"求生地图删除","地图删除"},priority=20,block=True,permission= Master)
rcon_to_server = on_command('rcon',aliases={"求生服务器指令","服务器指令","求生服务器控制台"},block=True,permission= Master)
check_path = on_command('l4_check',aliases={'求生路径'},priority=20,block=True,permission= Master)
smx_file = on_command('l4_smx',aliases={'求生插件'},priority=20,block=True,permission= Master)

# anne
anne_player = on_command('Ranne',aliases={"求生anne"},priority=25,block=True)
anne_bind = on_command('Rbind',aliases={'steam绑定','求生绑定','anne绑定'},priority=20,block=True)
del_bind = on_command('del_bind',aliases={'steam解绑','求生解绑','anne解绑'},priority=20,block=True)
prison = on_command('zl',aliases={'坐牢'},priority=20,block=True)
open_prison = on_command('kl',aliases={'开牢'},priority=20,block=True)

# updata = on_command('updata',aliases={'求生更新'},priority=20,block=True,permission= Master)
tan_jian = on_command('tj',aliases={'探监'},priority=20,block=True)

# 查询
queries = on_command('queries',aliases={'求生ip','求生IP'},priority=20,block=True)
add_queries = on_command('addq',aliases={"求生添加订阅"},priority=20,block=True,permission= Master)
del_queries = on_command('delq',aliases={"求生取消订阅"},priority=20,block=True,permission= Master)
show_queries = on_command('showq',aliases={"求生订阅"},priority=20,block=True)
join_server = on_command('ld_jr',aliases={"求生加入"},priority=20,block=True)
connect_rcon = on_command("Rrcon", aliases={"求生连接", '求生链接','求生rcon'}, priority=50, block=False)
end_connect = ['stop', '结束', '连接结束', '结束连接']
search_api = on_command('search',aliases={'求生三方'}, priority=20, block=True,permission= Master)
which_map = on_keyword(("是什么图"),priority=20, block=False)
reload_ip = on_command('l4_reload',aliases={'重载ip'},priority=30,permission=Master)

# 下载内容
up_workshop = on_command('workshop',aliases={'创意工坊下载','求生创意工坊'},priority=20,block=True)
vtf_make = on_command('vtf_make',aliases={'求生喷漆'},priority=20,block=True)

@help_.handle()
async def _():
    msg = [
        '=====求生机器人帮助=====',
        '1、电信服战绩查询【求生anne[id/steamid/@]】',
        '2、电信服绑定【求生绑定[id/steamid]】',
        '3、电信服状态查询【云xx】'
        '4、创意工坊下载【创意工坊下载[物品id/链接]】',
        '5、指定ip查询【求生ip[ip]】(可以是域名)',
        '6、求生喷漆制作【求生喷漆】',
        '6、本地服务器操作(略，详情看项目地址)',
    ]
    messgae = ''
    for i in msg:
        messgae += i + '\n'
    await help_.finish(messgae)

def get_session_id(event: MessageEvent) -> str:
    if isinstance(event, GroupMessageEvent):
        return f"group_{event.group_id}"
    else:
        return f"private_{event.user_id}"

matchers: Dict[str, List[Type[Matcher]]] = {}


    
async def get_des_ip():
    global ALL_HOST
    global ANNE_IP
    global matchers
    if l4_config.l4_tag == None:
        pass
    else:
        # try:
        #     qq = l4_config.l4_master[0]
        # except:
        #     qq = list(nonebot.get_bot().config.superusers)[0]
        # ALL_HOST.update(await seach_map(msg = l4_config.l4_tag,qq = qq, key=l4_config.l4_key,mode='ip'))
        def count_ips(ip_dict:dict):
            global ANNE_IP
            for key, value in ip_dict.items():
                if key in ['error_','success_']:
                    ip_dict.pop(key)
                    break
                count = len(value)
                logger.info(f'已加载：{key} | {count}个')
                if key == '云':
                    ANNE_IP = {key:value}
        sleep(1)
        count_ips(ALL_HOST)
        ip_anne_list=[] 
        try:
            ips = ALL_HOST['云']
            ip_anne_list = []
            for one_ip in ips:
                host,port = split_maohao(one_ip['ip'])
                ip_anne_list.append((one_ip['id'],host,port))
        except KeyError:
            pass
    
    
    get_ip = on_command('anne',aliases=server_key(),priority=80,block=True)
    @get_ip.handle()
    async def _(matcher:Matcher,start:str = CommandStart(),command: str = RawCommand(),args:Message = CommandArg()):
        global matchers
        if get_ip.plugin_name not in matchers:
            matchers[get_ip.plugin_name] = []
        matchers[get_ip.plugin_name].append(get_ip)
        if start:
            command = command.replace(start,'')
        if command == 'anne':
            command = '云'
        msg:str = args.extract_plain_text()
        if not msg:
            # 以图片输出全部当前
            if command in gamemode_list:
                this_ips = [d for l in ALL_HOST.values() for d in l if d.get('version') == command]
                igr = True
            else:
                this_ips:list = ALL_HOST[command]
                igr = False
            if not this_ips:
                matcher.finish('')
            ip_list = []
            for one_ip in this_ips:
                host,port = split_maohao(one_ip['ip'])
                ip_list.append((one_ip['id'],host,port))
            img = await qq_ip_queries_pic(ip_list,igr)
            if img:
                await matcher.finish(MessageSegment.image(img)) 
            else:
                await matcher.finish("服务器无响应")
        else:
            if not msg[0].isdigit():
                if any(mode in msg for mode in gamemode_list):
                    pass
                else:
                    return
            message = await json_server_to_tag_dict(command,msg)
            if len(message) == 0:
                # 关键词不匹配，忽略
                return
            ip = str(message['ip'])
            logger.info(ip)
            try:
                msg= await get_anne_server_ip(ip)
                await matcher.finish(msg)
            except (OSError,asyncio.exceptions.TimeoutError):
                await matcher.finish('服务器无响应')
    
           
    @tan_jian.handle()
    async def _(matcher:Matcher,event:MessageEvent):
        msg = await get_tan_jian(ip_anne_list,1)
        await matcher.finish(msg)  
        
    @prison.handle()
    async def _(matcher:Matcher,event:MessageEvent):
        msg = await get_tan_jian(ip_anne_list,2)
        await matcher.finish(msg)

    @open_prison.handle()
    async def _(matcher:Matcher,event:MessageEvent):

        msg = await get_tan_jian(ip_anne_list,3)
        await matcher.finish(msg)
        
    
    
async def init():
    global matchers
    # print('启动辣')
    await get_des_ip()
    
   
    
@driver.on_bot_connect
async def _():
    await init()