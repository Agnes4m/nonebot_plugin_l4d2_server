from nonebot.adapters.onebot.v11 import NoticeEvent,Bot,MessageEvent,Message,MessageSegment,GroupMessageEvent
from nonebot.params import CommandArg,ArgPlainText,RegexGroup
from nonebot.matcher import Matcher
from typing import Tuple
from time import sleep
from .config import *
from .utils import *
from .command import *
from nonebot.plugin import PluginMetadata
from .l4d2_data import sq_L4D2
from nonebot import get_driver
driver = get_driver()


__version__ = "0.1.6"
__plugin_meta__ = PluginMetadata(
    name="求生服务器操作",
    description='群内对服务器的简单操作',
    usage='求生服务器操作指令',
    extra={
        "version": __version__,
        "author": "Umamusume-Agnes-Digital <Z735803792@163.com>",
    },
)



"""相当于启动就检查数据库"""


@up.handle()
async def _(event: NoticeEvent, matcher: Matcher):
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
    # user_id = args['user_id']
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
    # 没有参数则从db里找数据
    msg = await search_anne(name,usr_id)
    if type(msg)==str:
        await anne_player.finish(msg)
    else:
        await anne_player.finish(MessageSegment.image(msg))
        
@anne_server.handle()
async def _():
    await anne_server.send('正在查询，方式是谷歌浏览器')
    msg = anne_servers()
    if len(msg)==0:
        await anne_server.finish('服务器超市了')
    else:
        if l4_image:
            await find_vpk.finish(MessageSegment.image(text_to_png(msg)))
        else:
            await anne_server.finish(msg)
    
    
@anne_bind.handle()
async def _(event:MessageEvent,args:Message = CommandArg()):
    tag = args.extract_plain_text()
    tag = tag.strip()
    if tag=="" or tag.isspace():
        await anne_bind.finish("虚空绑定?")
    usr_id = str(event.user_id)
    nickname = event.sender.card or event.sender.nickname
    msg = await bind_steam(usr_id,tag,nickname)
    await anne_bind.finish(msg)

@del_bind.handle()
async def _(event:MessageEvent):
    usr_id = event.user_id
    await del_bind.finish(name_exist(usr_id))

@rcon_to_server.handle()
async def _(matcher:Matcher,args:Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg:
        matcher.set_arg("command",args)

@rcon_to_server.got("command",prompt="请输入向服务器发送的指令")
async def _(tag:str = ArgPlainText("command")):
    tag = tag.strip()
    msg = await command_server(tag)
    if l4_image:
        await rcon_to_server.finish(MessageSegment.image(text_to_png(msg)))
    else:
        await rcon_to_server.finish(msg,reply_message = True)
        
@queries.handle()
async def _(matcher:Matcher,args:Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg:
        matcher.set_arg("ip",args)

@queries.got("ip",prompt="请输入ip,格式如中括号内【127.0.0.1】【114.51.49.19:1810】")
async def _(tag:str = ArgPlainText("ip")):
    ip = split_maohao(tag)
    msg = await queries_server(ip)
    await queries.finish(msg)
    

@add_queries.handle()
async def _(event:GroupMessageEvent,args:Message = CommandArg()):
    msg = args.extract_plain_text()
    [host,port] = split_maohao(msg)
    group_id = event.group_id
    msg = await add_ip(group_id,host,port)
    await add_queries.finish(msg)

# @del_queries.handle()
# async def _(event:GroupMessageEvent,matcher:Matcher,args:Message = CommandArg()):
#     msg = args.extract_plain_text()
#     [host,port] = split_maohao(msg)
#     group_id = event.group_id
#     msg = await add_ip(group_id,host,port)    
@show_queries.handle()
async def _(event:GroupMessageEvent):
    group_id = event.group_id
    msg = await show_ip(group_id)    

            
    
@driver.on_shutdown
async def close_db():
    """关闭数据库"""
    sq_L4D2._close()