from nonebot.adapters.onebot.v11 import NoticeEvent,Bot,MessageEvent,Message,MessageSegment,GroupMessageEvent
from nonebot.params import CommandArg,ArgPlainText,RegexGroup
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from typing import Tuple
from time import sleep
from .config import *
from .utils import *
from .command import *
from .l4d2_image.steam import url_to_byte
from nonebot.plugin import PluginMetadata
from .l4d2_data import sq_L4D2
from .l4d2_anne.server import updata_anne_server,get_anne_ip
from nonebot import get_driver
import tempfile
driver = get_driver()


__version__ = "0.2.1"
__plugin_meta__ = PluginMetadata(
    name="求生之路小助手",
    description='群内对有关求生之路的查询和操作',
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
    try:
        await find_vpk.finish(MessageSegment.image(text_to_png(msg)))
    except OSError:
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
    if len(msg)==0:
        await add_queries.finish('请在该指令后加入参数，例如【114.51.49.19:1810】')
    [host,port] = split_maohao(msg)
    group_id = event.group_id
    msg = await add_ip(group_id,host,port)
    await add_queries.finish(msg)

@del_queries.handle()
async def _(event:GroupMessageEvent,matcher:Matcher,args:Message = CommandArg()):
    msg = args.extract_plain_text()
    if not msg.isdigit():
        await del_queries.finish('请输入正确的序号数字')
    group_id = event.group_id
    msg = await del_ip(group_id,msg)
    await del_queries.finish(msg)
   
@show_queries.handle()
async def _(event:GroupMessageEvent):
    group_id = event.group_id
    msg = await show_ip(group_id)
    if type(msg) == str:
        await show_queries.finish(msg)
    else:
        await show_queries.finish(MessageSegment.image(msg))

@join_server.handle()
async def _(args:Message = CommandArg()):
    msg = args.extract_plain_text()
    url = await get_number_url(msg)
    await join_server.finish(url)
    
        
@up_workshop.handle()
async def _(matcher:Matcher,args:Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg:
        matcher.set_arg("ip",args)
    
@up_workshop.got("ip",prompt="请输入创意工坊网址或者物品id")
async def _(matcher:Matcher,state:T_State,tag:str = ArgPlainText("ip")):
    msg = await workshop_msg(tag)
    if not msg:
        await up_workshop.finish('没有这个物品捏')
    pic = await url_to_byte(msg['图片地址'])
    message = ''
    for item,value in msg.items():
        if item in ['图片地址','下载地址']:
            continue
        message += item + ':' + value + '\n'
    state['dic'] = msg
    await up_workshop.send(MessageSegment.image(pic) + Message(message))
    
@up_workshop.got("is_sure",prompt='如果需要上传，请发送 "yes"')    
async def _(matcher: Matcher,bot:Bot,event:GroupMessageEvent,state:T_State):
    is_sure = str(state["is_sure"])
    data_dict:dict = state['dic']
    logger.info('开始上传')
    data_file = await url_to_byte(data_dict['下载地址'])
    file_name = data_dict['名字']+ '.vpk'
    await up_workshop.send('获取地址成功，尝试上传')
    if is_sure == 'yes':
        await upload_file(bot, event, data_file, file_name)
    else:
        await matcher.finish('已取消上传')
    
    
async def upload_file(bot: Bot, event: MessageEvent, file_data: bytes, filename: str):
    """上传临时文件"""
    with tempfile.NamedTemporaryFile("wb+") as f:
        f.write(file_data)
        if isinstance(event, GroupMessageEvent):
            await bot.call_api(
                "upload_group_file", group_id=event.group_id, file=f.name, name=filename
            )
        else:
            await bot.call_api(
                "upload_private_file", user_id=event.user_id, file=f.name, name=filename
            )

@updata.handle()
async def _():
    msg = await updata_anne_server()
    if msg:
        n = len(msg)
        await updata.finish(f'更新成功，目前有{n}个ip')
    await updata.finish('获取失败了')

@get_anne.handle()
async def _(args:Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg.isdigit():
        msg = '云' + msg
        logger.info(msg)
        ip = await get_anne_ip(msg)
        if ip:
            message = await get_anne_server_ip(ip)
            await get_anne.finish(message)
    
@read_ip.handle()
async def _(event:GroupMessageEvent):
    group = event.group_id
    ip_list = []
    keys = ANNE_IP.keys()
    for key in keys:
        ip = ANNE_IP[key]
        host,port = split_maohao(ip)
        ip_list.append((key,group,host,port))
    img = await qq_ip_queries_pic(ip_list)
    await read_ip.finish(MessageSegment.image(img))

@tan_jian.handle()
async def _(event:MessageEvent):
    group = event.user_id
    await tan_jian.send('正在寻找牢房...')
    ip_list = []
    keys = ANNE_IP.keys()
    for key in keys:
        key:str
        if key.startswith('云'):
            ip = ANNE_IP[key]
            host,port = split_maohao(ip)
            ip_list.append((key,group,host,port))
    msg = await get_tan_jian(ip_list)
    await tan_jian.finish(msg)
            

@driver.on_shutdown
async def close_db():
    """关闭数据库"""
    sq_L4D2._close()