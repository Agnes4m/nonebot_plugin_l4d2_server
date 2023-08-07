from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_saa import Image, MessageFactory

from ..l4d2_utils.utils import (
    at_to_usrid,
    get_message_at,
)
from .utils import anne_message, del_player, write_player

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


@anne_player.handle()
async def _(matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    # 只能v11
    name = args.extract_plain_text()
    name = name.strip()
    at = await get_message_at(event.json())
    usr_id = at_to_usrid(at)
    if not usr_id:
        usr_id = event.user_id  # type: ignore
    # 没有参数则从db里找数据
    msg = await search_anne(name, str(usr_id))
    if isinstance(msg, str):
        await matcher.finish(msg)
    elif isinstance(msg, bytes):
        await MessageFactory([Image(msg)]).finish()


@anne_bind.handle()
async def _(matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    # 只能v11
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


async def bind_steam(id_: str, msg: str, nickname: str):
    """绑定qq-steam"""
    return await write_player(id_, msg, nickname)


async def search_anne(name: str, usr_id: str):
    """获取anne成绩"""
    return await anne_message(name, usr_id)


def name_exist(id_: str):
    """删除绑定信息"""
    return del_player(id_)
