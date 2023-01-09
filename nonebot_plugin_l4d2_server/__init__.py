from nonebot import on_notice,on_command,on_regex
from nonebot.adapters.onebot.v11 import NoticeEvent,Bot,MessageEvent,Message,MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg,ArgPlainText,RegexGroup
from nonebot.matcher import Matcher
import re
from typing import Tuple
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)
from time import sleep
from .config import *
from .utils import *

from nonebot.plugin import PluginMetadata
__version__ = "0.1.3"
__plugin_meta__ = PluginMetadata(
    name="求生服务器操作",
    description='群内对服务器的简单操作',
    usage='求生服务器操作指令',
    extra={
        "version": __version__,
        "author": "Umamusume-Agnes-Digital <Z735803792@163.com>",
    },
)


Master = SUPERUSER | GROUP_ADMIN | GROUP_OWNER 

up = on_notice()
rename_vpk = on_regex(
        r"^求生地图\s*(\S+.*?)\s*(改|改名)?\s*(\S+.*?)\s*$",
    flags=  re.S,
    block= True,
    priority= 20,
    permission= Master,
)
# 服务器
find_vpk = on_command("l4_map",aliases={"求生地图","查看求生地图"},priority=25,block=True)
del_vpk = on_command("l4_del_map",aliases={"求生地图删除","地图删除"},priority=20,block=True,permission= Master)

# anne
anne_player = on_command('Ranne',aliases={"求生anne"},priority=25,block=True)
anne_server = on_command('anneip',aliases={'求生anne服务器','求生药役服务器'},priority=20,block=True)
steam_bind = on_command('Rbind',aliases={'steam绑定','求生绑定','anne绑定'},priority=20,block=True)
del_bind = on_command('del_bind',aliases={'steam解绑','求生解绑','anne解绑'},priority=20,block=True)

@up.handle()
async def _(bot:Bot ,event: NoticeEvent, matcher: Matcher):
    # 检查下载路径是否存在
    if not Path(l4_file).exists():
        await up.finish("你填写的路径不存在辣")
    if not Path(map_path).exists():
        await up.finish("这个路径并不是求生服务器的路径，请再看看罢")
    args = event.dict()
    if args['notice_type'] != 'offline_file':  # 只响应私聊
        await matcher.finish()
    url = args['file']['url']
    name: str = args['file']['name']
    user_id = args['user_id']
    # 如果不符合格式则忽略
    if not name.endswith(file_format):
        return
    await up.send('已收到文件，开始下载')
    sleep(1)   # 等待一秒防止因为文件名获取出现BUG
    
    down_file = Path(map_path,name)
    if get_file(url,down_file) == "寄":
        await up.finish("获取文件失败，可能文件已损坏")
    else:
        pass
    
    original_vpk_files = []
    original_vpk_files = get_vpk(original_vpk_files,map_path)
    msg = open_packet(name,down_file)
    await up.send(msg)
    
    sleep(1)
    extracted_vpk_files = []
    extracted_vpk_files = get_vpk(extracted_vpk_files,map_path)
    logger.info(extracted_vpk_files)
    # 获取新增vpk文件的list
    vpk_files = list(set(extracted_vpk_files) - set(original_vpk_files))
    if vpk_files:
        logger.info('检查到新增文件')
        mes = "解压成功，新增以下几个vpk文件"
    else:
        mes = "你可能上传了相同的文件，或者解压失败了捏"
    await up.finish(mes_list(mes,vpk_files))
    
@find_vpk.handle()
async def _(bot:Bot,event: MessageEvent):    
    name_vpk = []
    name_vpk = get_vpk(name_vpk,map_path)
    logger.info("获取文件列表成功")
    mes = "当前服务器下有以下vpk文件"
    msg = mes_list(mes,name_vpk).replace(" ","")
    if l4_image:
        await find_vpk.finish(MessageSegment.image(text_to_png(msg)))
    else:
        await find_vpk.finish(msg)

@del_vpk.handle()
async def _(matcher:Matcher,args:Message = CommandArg()):
    num1 = args.extract_plain_text()
    if num1:
        matcher.set_arg("num",args)

@del_vpk.got("num",prompt="你要删除第几个序号的地图(阿拉伯数字)")
async def _(tag:int = ArgPlainText("num")):
    tag = tag.replace(' ','')
    vpk_name = del_map(tag,map_path)
    await del_vpk.finish('已删除地图：' + vpk_name)
    
@rename_vpk.handle()
async def _(matched: Tuple[int,str, str] = RegexGroup(),):
    num,useless,rename = matched
    logger.info('检查是否名字是.vpk后缀')
    if not rename.endswith('.vpk'):
        rename = rename + '.vpk'
    logger.info('尝试改名')
    try:
        map_name = rename_map(num,rename,map_path)
        if map_name:
            await rename_vpk.finish('改名成功\n原名:'+ map_name +'\n新名称:' + rename)
    except ValueError:
        await rename_vpk.finish('参数错误,请输入格式如【求生地图 5 改名 map.vpk】,或者输入【求生地图】获取全部名称')
        
@anne_player.handle()
async def _(event:MessageEvent,args:Message = CommandArg()):
    name = args.extract_plain_text()
    name = name.strip()
    usr_id = event.user_id
    at = await get_message_at(event.json())
    usr_id = at_to_usrid(usr_id,at)
    # 没有参数则从json里找数据
    msg = await search_anne(name,usr_id)
    if type(msg)==str:
        await anne_player.finish(msg)
    else:
        await anne_player.finish(MessageSegment.image(msg))
        
@anne_server.handle()
async def _():
    msg = anne_servers()
    if len(msg)==0:
        await anne_server.finish('服务器超市了')
    else:
        if l4_image:
            await find_vpk.finish(MessageSegment.image(text_to_png(msg)))
        else:
            await anne_server.finish(msg)
    
    
@steam_bind.handle()
async def _(event:MessageEvent,args:Message = CommandArg()):
    tag = args.extract_plain_text()
    tag = tag.strip()
    if tag=="" or tag.isspace():
        await steam_bind.finish("虚空绑定?")
    usr_id = str(event.user_id)
    nickname = event.sender.card or event.sender.nickname
    msg = bind_steam(usr_id,tag,nickname)
    await steam_bind.finish(msg)

@del_bind.handle()
async def _(event:MessageEvent):
    usr_id = event.user_id
    await del_bind.finish(name_exist(usr_id))
    