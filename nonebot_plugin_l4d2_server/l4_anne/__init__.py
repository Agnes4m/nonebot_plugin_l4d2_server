from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, Depends
from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_datastore import get_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from ..utils.api.request import L4API
from ..utils.database.models import SteamUser


async def get_anne_player_out():
    return "\n".join(str(item) for item in (await L4API.get_anne_player())[1:]).strip()

anne_bind = on_command("l4bind", aliases={"l4绑定"})
anne_player = on_command("l4player", aliases={"anne在线"}, block=True, priority=1)
anne_search = on_command("l4search", aliases={"anne搜索"})

@anne_bind.handle()
async def _(ev: Event, args: Message = CommandArg()):
    user_id = ev.get_user_id()
    name = args.extract_plain_text().strip()
    if not name or not user_id:
        return
    await UniMessage.text("to do").finish()

@anne_player.handle()
async def _():
    await UniMessage.text(await get_anne_player_out()).finish()
    
@anne_search.handle()
async def _(args: Message = CommandArg()):
    name: str = args.extract_plain_text().strip()
    
        
anne_bind = on_command("l4bind", aliases={"l4绑定", "anne绑定"}, priority=5, block=True)
@anne_bind.handle()
async def _(ev: Event, args: Message = CommandArg(),session: AsyncSession = Depends(get_session)):
    arg: str = args.extract_plain_text()
    if not arg:
        await UniMessage.text("虚空绑定？").finish()
    # 判断参数是steam64位id还是steamid3
    if len(arg) == 17:
   
        stmt = select(SteamUser).where(SteamUser.userid == ev.get_user_id())  
        result = await session.execute(stmt) 
        users = result.scalars().all()
        if len(users) >= 1:  
            user = users[0]
            user.SteamID64 = arg
        else:
            user = SteamUser(
                userid = ev.get_user_id,
                mode = arg,
                )
        
    elif arg.startswith("STEAM_"):
        stmt = select(SteamUser).where(SteamUser.userid == ev.get_user_id)  
        result = await session.execute(stmt) 
        users = result.scalars().all()
        if len(users) >= 1:  
            user = users[0]
            user.SteamID = arg
        else:
            user = SteamUser(
                userid = ev.get_user_id(),
                mode = arg,
                )
    return await UniMessage.text("绑定成功").finish()


anne_del = on_command("l4del", aliases={"l4删除", "anne删除"}, priority=5, block=True)
@anne_del.handle()
async def _(ev: Event,session: AsyncSession = Depends(get_session)):

    await session.delete(SteamUser(userid = ev.get_user_id()))
    return await UniMessage.text("删除成功").finish()
