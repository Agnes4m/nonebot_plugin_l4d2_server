from nonebot import on_command, require
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, Depends
from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_orm import Model, async_scoped_session, get_session

from ..utils.api.request import L4API
from ..utils.database.models import SteamUser
from ..utils.utils import get_message_at


async def get_anne_player_out():
    return "\n".join(str(item) for item in (await L4API.get_anne_player())[1:]).strip()

anne_bind = on_command("l4bind", aliases={"l4绑定", "anne绑定"}, priority=5, block=True)
anne_player = on_command("l4player", aliases={"anne在线"}, block=True, priority=1)
anne_search = on_command("l4search", aliases={"anne搜索"})
anne_rank = on_command("Ranne", aliases={"anne成绩"}, block=True, priority=1)

anne_del = on_command("l4del", aliases={"l4删除", "anne删除", "l4解绑", "anne解绑"}, priority=5, block=True)

@anne_player.handle()
async def _():
    await UniMessage.text(await get_anne_player_out()).finish()
    
@anne_search.handle()
async def _(args: Message = CommandArg()):
    name: str = args.extract_plain_text().strip()
    
        
@anne_bind.handle()
async def _(ev: Event, args: Message = CommandArg()):
    arg: str = args.extract_plain_text()
    if not arg:
        await UniMessage.text("虚空绑定？").finish()
    
    user, ones =await SteamUser.get_or_create(userid=ev.get_user_id())
    if ones:
        # 更新表
        if len(arg) == 17:
            # steamid64
            user.SteamID64 = arg
            msg = "绑定steamid64"

        elif arg.startswith("STEAM_"):
            # steamid
            user.SteamID = arg
            msg = "绑定steamid"

        else:
            # name
            user.Name = arg
            msg = "绑定名字"
    else:
        if len(arg) == 17:
            # steamid64
            await SteamUser.create(userid=ev.get_user_id(), SteamID64=arg)
            msg = "绑定steamid64"

        elif arg.startswith("STEAM_"):
            # steamid
            await SteamUser.create(userid=ev.get_user_id(), SteamID=arg)
            msg = "绑定steamid"
        else:
            # name
            await SteamUser.create(userid=ev.get_user_id(), Name=arg)
            msg = "绑定名字"
            
    return await UniMessage.text(f"{msg}成功").finish()


@anne_del.handle()
async def _(ev: Event):
    if record := await SteamUser.get_or_none(message_id=ev.get_user_id()):
        await record.delete()
        await record.save()
        return await UniMessage.text("删除成功").finish()
    return await UniMessage.text("没有绑定").finish()
    

@anne_rank.handle()
async def _(ev: Event,args: Message = CommandArg()):
    uid = await get_message_at(str(ev.json()))
    if uid is None:
        uid = int(ev.get_user_id())
    steamid = ""
    arg: str = args.extract_plain_text().strip()
    if arg.startswith("STEAM_"):
        steamid = arg
    else:
        ...
    if not steamid:
        await UniMessage.text("未找到玩家,请使用指令`l4搜索`查找").finish()
    # await UniMessage.text(await get_anne_rank_out(steamid)).finish()    