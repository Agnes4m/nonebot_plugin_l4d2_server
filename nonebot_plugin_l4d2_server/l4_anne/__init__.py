from nonebot import log as log
from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage

from nonebot_plugin_l4d2_server.utils.api.models import AnneSearch

from ..utils.api.request import L4API
from ..utils.database.models import SteamUser
from ..utils.utils import get_message_at


async def get_anne_player_out():
    return "\n".join(str(item) for item in (await L4API.get_anne_player())[1:]).strip()


anne_bind = on_command("l4bind", aliases={"l4绑定", "anne绑定"}, priority=5, block=True)
anne_player = on_command("l4player", aliases={"anne在线"}, block=True, priority=1)
anne_search = on_command("l4search", aliases={"anne搜索"})
anne_rank = on_command("Ranne", aliases={"anne成绩"}, block=True, priority=1)

anne_del = on_command(
    "l4del", aliases={"l4删除", "anne删除", "l4解绑", "anne解绑"}, priority=5, block=True
)


@anne_player.handle()
async def _():
    await UniMessage.text(await get_anne_player_out()).finish()


@anne_search.handle()
async def _(args: Message = CommandArg()):
    name: str = args.extract_plain_text().strip()
    user_list: list[AnneSearch] = await L4API.get_anne_steamid(name)
    msg = ""
    for index, user in enumerate(user_list, start=1):
        msg += f"""{index}. {user["name"]} | {user["rank"]} | [{user["score"]}]
        {user["steamid"]}"""
    if msg:
        await UniMessage.text("\n".join(msg.splitlines())).finish()
    else:
        await UniMessage.text("没有找到玩家").finish()


@anne_bind.handle()
async def _(ev: Event, args: Message = CommandArg()):
    arg: str = args.extract_plain_text()
    if not arg:
        await UniMessage.text("虚空绑定？").finish()

    user = await SteamUser.get_or_none(userid=int(ev.get_user_id()))
    if user is None:
        user = await SteamUser.create(userid=int(ev.get_user_id()))

    if len(arg) == 17:
        # steamid64
        logger.info(f"SteamID64:{arg}")
        user.SteamID64 = arg
        msg = "绑定steamid64"

    elif arg.startswith("STEAM_"):
        # steamid
        logger.info(f"SteamID:{arg}")
        user.SteamID = arg
        msg = "绑定steamid"

    else:
        # name
        logger.info(f"Name:{arg}")
        user.Name = arg
        msg = "绑定名字"
    await user.save()

    return await UniMessage.text(f"{msg}成功").finish()


@anne_del.handle()
async def _(ev: Event):
    if record := await SteamUser.get_or_none(userid=int(ev.get_user_id())):
        logger.info(f"删除用户:{record}")
        await record.delete()
        await record.save()
        return await UniMessage.text("删除成功").finish()
    return await UniMessage.text("没有绑定信息呢").finish()


@anne_rank.handle()
async def _(ev: Event, args: Message = CommandArg()):
    uid = await get_message_at(str(ev.json()))
    if uid is None:
        uid = int(int(ev.get_user_id()))
    steamid = ""
    arg: str = args.extract_plain_text().strip()
    if arg.startswith("STEAM_"):
        steamid = arg
    else:
        ...
    if not steamid:
        await UniMessage.text("未找到玩家,请使用指令`l4搜索`查找").finish()
    # await UniMessage.text(await get_anne_rank_out(steamid)).finish()
