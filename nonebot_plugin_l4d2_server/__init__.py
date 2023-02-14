
from nonebot_plugin_txt2img import Txt2Img
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
from .l4d2_anne.server import get_anne_ip
from nonebot import get_driver
from .l4d2_image.vtfs import img_to_vtf
from .l4d2_queries.ohter import load_josn
from .l4d2_queries.qqgroup import write_json
from .l4d2_file import updown_l4d2_vpk
from .txt_to_img import mode_txt_to_img
driver = get_driver()


__version__ = "0.2.5.5"
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

# @up.handle()
# async def _(matcher:Matcher,event: NoticeEvent,state:T_State):
#     # 检查下载路径是否存在
#     logger.info('监测到文件了，判断判断')
#     if not Path(l4_file).exists():
#         await up.finish("你填写的路径不存在辣")
#     if not Path(map_path).exists():
#         await up.finish("这个路径并不是求生服务器的路径，请再看看罢")
#     args = event.dict()
#     if args['notice_type'] != 'offline_file':  # 响应私聊,group_upload只有管理员
#         logger.info('这是一个群文件')
#         superuse:list = nonebot.get_driver().config.l4_master
#         if str(args['user_id']) not in superuse:
#             await up.finish()
#     state['file'] = args['file']
#     logger.info('第一段结束')


# @up.got("is_sure",prompt="监测到地图，请发送yes确认上传地图'")    
# async def _(state:T_State):
#     logger.info('第二段')
#     is_sure = str(state["is_sure"]).strip()
#     name:str = state['file']['name']
#     url:str = state['file']['url']
#     logger.info('开始判断')
#     if is_sure == 'yes':
#         if not name.endswith(file_format):
#             return
#         await up.send('已收到文件，开始下载')
#         sleep(1)   # 等待一秒防止因为文件名获取出现BUG
#         vpk_files =  await updown_l4d2_vpk(map_path,name,url)
#         if vpk_files:
#             logger.info('检查到新增文件')
#             mes = "解压成功，新增以下几个vpk文件"
#         else:
#             mes = "你可能上传了相同的文件，或者解压失败了捏"
#         await up.finish(mes_list(mes,vpk_files))

@up.handle()
async def _(matcher:Matcher,event: GroupUploadNoticeEvent):
    if isinstance(event, GroupUploadNoticeEvent):
        txt = event.dict()
        user_id = txt['user_id']
        # 如果不符合格式则忽略
        matcher.set_arg('args',event)
    txt = event.dict()
    matcher.set_arg('args',event)
    # 检查下载路径是否存在
    # logger.info('检查下载路径是否存在')
    # if not Path(l4_file).exists():
    #     await up.finish("你填写的路径不存在辣")
    # if not Path(map_path).exists():
    #     await up.finish("这个路径并不是求生服务器的路径，请再看看罢")
    #     # args = event.dict()
    # # if args['notice_type'] != 'offline_file':  # 群聊值响应超管
    # #     return
    # url = txt['file']['url']
    # name: str = txt['file']['name']
    # # user_id = txt['user_id']
    # # 如果不符合格式则忽略
    # if not name.endswith(file_format):
    #     return
    # await up.send('已收到文件，开始下载')
    # sleep(1)   # 等待一秒防止因为文件名获取出现BUG
    # vpk_files = await updown_l4d2_vpk(map_path,name,url)
    # if vpk_files:
    #     logger.info('检查到新增文件')
    #     mes = "解压成功，新增以下几个vpk文件"
    # else:
    #     mes = "你可能上传了相同的文件，或者解压失败了捏"
            
    # await up.finish(mes_list(mes,vpk_files))


@up.got("is_sure",prompt="请发送yes确认上传地图'")    
async def _(matcher: Matcher):
    txt:NoticeEvent = matcher.get_arg('txt')
    args = txt.dict()
    is_sure = str(matcher.get_arg('is_sure')).strip()
    if is_sure == "yes":
        # 检查下载路径是否存在
        logger.info('检查下载路径是否存在')
        if not Path(l4_file).exists():
            await up.finish("你填写的路径不存在辣")
        if not Path(map_path).exists():
            await up.finish("这个路径并不是求生服务器的路径，请再看看罢")
        # args = event.dict()
        # if args['notice_type'] != 'offline_file':  # 群聊值响应超管
        url = args['file']['url']
        name: str = args['file']['name']
        # user_id = args['user_id']
        # 如果不符合格式则忽略
        if not name.endswith(file_format):
            return
        await up.send('已收到文件，开始下载')
        sleep(1)   # 等待一秒防止因为文件名获取出现BUG
        vpk_files = await updown_l4d2_vpk(map_path,name,url)
        if vpk_files:
            logger.info('检查到新增文件')
            mes = "解压成功，新增以下几个vpk文件"
        elif vpk_files == None:
            await up.finish('文件错误')
        else:
            mes = "你可能上传了相同的文件，或者解压失败了捏"
            
        await up.finish(mes_list(mes,vpk_files))
    else:
        await up.finish('已取消上传')
    
@find_vpk.handle()
async def _(bot:Bot,event: MessageEvent):    
    name_vpk = []
    name_vpk = get_vpk(name_vpk,map_path)
    logger.info("获取文件列表成功")
    mes = "当前服务器下有以下vpk文件"
    msg = ''
    msg = mes_list(msg,name_vpk).replace(" ","")
    
    await find_vpk.finish(mode_txt_to_img(mes,msg))
    # await find_vpk.finish(msg)

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
    at = await get_message_at(event.json())
    if at:
        usr_id = at_to_usrid(at)
    else:
        usr_id = event.user_id
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
        await rcon_to_server.finish(mode_txt_to_img('服务器返回',msg))
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
async def _(state:T_State,tag:str = ArgPlainText("ip")):
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
    if is_sure == 'yes':
        data_dict:dict = state['dic']
        logger.info('开始上传')
        data_file = await url_to_byte(data_dict['下载地址'])
        file_name = data_dict['名字']+ '.vpk'
        await up_workshop.send('获取地址成功，尝试上传')
        await upload_file(bot, event, data_file, file_name)
    else:
        await up_workshop.finish('已取消上传')
    


@updata.handle()
async def _(args:Message = CommandArg()):
    msg = args.extract_plain_text()
    if not msg:
        load_josn()
        reload_ip()
        await updata.finish('已更新缓存数据')
    else:
        message = await write_json(msg)
        await updata.finish(message)

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
    msg = await get_tan_jian(ip_list,1)
    await tan_jian.finish(msg)

@get_ip.handle()
async def _(command: str = RawCommand(),args:Message = CommandArg()):
    logger.info(command)
    msg:str = args.extract_plain_text()
    logger.info(msg)
    message = await json_server_to_tag_dict(command,msg)
    if len(message) == 0:
        # 关键词不匹配，忽略
        return
    ip = str(message['host']) + ':' + str(message['port'])
    logger.info(ip)
    msg= await get_anne_server_ip(ip)
    await get_ip.finish(msg)

            
@vtf_make.handle()
async def _(matcher:Matcher,state:T_State,args:Message = CommandArg()):
    msg:str = args.extract_plain_text()
    if msg not in ['拉伸','填充','覆盖','']:
        await vtf_make.finish('错误的图片处理方式')
    if msg == '':
        msg = '拉伸'
    state['way'] = msg
    logger.info('方式',msg)
    
@vtf_make.got("image",prompt="请发送喷漆图片")
async def _(bot:Bot,event:MessageEvent,state:T_State,tag = Arg("image")):
    pic_msg:MessageSegment =  state["image"][0]
    pic_url = pic_msg.data["url"]
    logger.info(pic_url)
    logger.info(type(pic_url))
    tag = state['way']
    pic_bytes = await url_to_byte(pic_url)
    img_io = await img_to_vtf(pic_bytes,tag)
    img_bytes = img_io.getbuffer()
    usr_id = event.user_id
    file_name:str = str(usr_id) + '.vtf'
    await upload_file(bot, event, img_bytes, file_name)


@prison.handle()
async def _(event:MessageEvent):
    group = event.user_id
    await tan_jian.send('正在寻找缺人...')
    ip_list = []
    keys = ANNE_IP.keys()
    for key in keys:
        key:str
        if key.startswith('云'):
            ip = ANNE_IP[key]
            host,port = split_maohao(ip)
            ip_list.append((key,group,host,port))
    msg = await get_tan_jian(ip_list,2)
    await tan_jian.finish(msg)

@open_prison.handle()
async def _(event:MessageEvent):
    group = event.user_id
    await tan_jian.send('正在寻找空房...')
    ip_list = []
    keys = ANNE_IP.keys()
    for key in keys:
        key:str
        if key.startswith('云'):
            ip = ANNE_IP[key]
            host,port = split_maohao(ip)
            ip_list.append((key,group,host,port))
    msg = await get_tan_jian(ip_list,3)
    await tan_jian.finish(msg)

@driver.on_shutdown
async def close_db():
    """关闭数据库"""
    sq_L4D2._close()
