from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna.uniseg import UniMessage

# from .l4d2_file.input_json import *
from ..l4d2_utils.config import MASTER
from ..l4d2_utils.utils import at_to_usrid, get_message_at
from .server import updata_anne_server
from .utils import bind_steam, name_exist, search_anne

# anne
anne_player = on_command("Ranne", aliases={"求生anne"}, priority=25, block=True)
anne_bind = on_command(
    "Rbind",
    aliases={"steam绑定", "求生绑定", "anne绑定"},
    priority=20,
    block=True,
)
del_bind = on_command(
    "del_bind",
    aliases={"steam解绑", "求生解绑", "anne解绑"},
    priority=20,
    block=True,
)
updata = on_command(
    "updata_anne",
    aliases={"求生更新anne"},
    priority=20,
    block=True,
    permission=MASTER,
)


@anne_player.handle()
async def _(matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text()
    name = name.strip()
    at = await get_message_at(event.json())
    usr_id = at_to_usrid(at)
    if not usr_id:
        usr_id = event.user_id
    # 没有参数则从db里找数据
    msg = await search_anne(name, str(usr_id))
    if isinstance(msg, str):
        await matcher.finish(msg)
    elif isinstance(msg, bytes):
        await UniMessage.image(raw=msg).send()


@anne_bind.handle()
async def _(matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    tag = args.extract_plain_text()
    tag = tag.strip()
    if tag == "" or tag.isspace():
        await matcher.finish("虚空绑定?")
    usr_id = str(event.user_id)
    nickname = event.sender.card or event.sender.nickname
    if not nickname:
        nickname = "宁宁"
    msg = await bind_steam(usr_id, tag, nickname)
    await matcher.finish(msg)


@del_bind.handle()
async def _(matcher: Matcher, event: MessageEvent):
    usr_id = event.user_id
    msg = name_exist(str(usr_id))
    if not msg:
        return
    await matcher.finish(msg)


@del_bind.handle()
async def _(matcher: Matcher, event: MessageEvent):
    usr_id = event.user_id
    msg = name_exist(str(usr_id))
    if not msg:
        return
    await matcher.finish(msg)


@updata.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    """更新"""
    if args:
        # 占位先，除了电信服还有再加
        ...
    anne_ip_dict = await updata_anne_server()
    if not anne_ip_dict:
        await matcher.finish("网络开小差了捏")
    server_number = len(anne_ip_dict["云"])
    await matcher.finish(f"更新成功\n一共更新了{server_number}个电信anne服ip")
