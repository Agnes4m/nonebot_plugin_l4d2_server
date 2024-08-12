from nonebot import log as log
from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage

from ..utils.api.request import L4API
from ..utils.database.models import SteamUser
from ..utils.utils import get_message_at
from .ranne import get_anne_rank_out

anne_bind = on_command("Banne", aliases={"l4绑定", "anne绑定"}, priority=5, block=True)
anne_search = on_command("Sanne", aliases={"anne搜索"})
anne_rank = on_command("Ranne", aliases={"anne成绩"}, block=True, priority=1)

anne_del = on_command(
    "Danne",
    aliases={"l4删除", "anne删除", "l4解绑", "anne解绑"},
    priority=5,
    block=True,
)


@anne_search.handle()
async def _(args: Message = CommandArg()):
    name: str = args.extract_plain_text().strip()
    print(name)
    user_list = await L4API.get_anne_steamid(name)
    if user_list is None:
        await UniMessage.text("未找到玩家").finish()
    msg = f"---有{len(user_list)}个玩家---"
    for index, user in enumerate(user_list, start=1):
        if index >= 10:
            break
        msg += f"""
        {index}. {user["name"]} | [{user["score"]}] | {user["play_time"]}
        {user["steamid"]}
        """
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
    logger.info(f"arg:{arg}")
    # 优先从数据库查询
    if not arg:
        msg = await SteamUser.get_or_none(userid=uid)
        if msg is not None:
            steamid = msg.SteamID
            if not steamid:
                name = msg.Name
                if not name:
                    await UniMessage.text("未绑定名字/steamid").finish()
                msg_dict = await L4API.get_anne_steamid(name)
                if not msg_dict:
                    await UniMessage.text("绑定的昵称找不到呢").finish()
                steamid = msg_dict[0]["steamid"]
            logger.info(f"steamid:{steamid}")

    # 再从arg中查找
    else:
        if arg.startswith("STEAM_"):
            steamid = arg
        else:
            arg_dict = await L4API.get_anne_steamid(arg)
            if not arg_dict:
                await UniMessage.text("未找到该昵称玩家").finish()
            steamid = arg_dict[0]["steamid"]
    if not steamid:
        await UniMessage.text("未找到玩家,请使用指令`l4搜索`查找").finish()
    out_msg = await get_anne_rank_out(steamid)
    if out_msg is None:
        await UniMessage.text("未找到玩家").finish()
    await UniMessage.text(out_msg).finish()
