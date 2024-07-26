"""
* Copyright (c) 2023, Agnes Digital
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from typing import List, Optional

from nonebot import require
from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.plugin import on_command

require("nonebot_plugin_orm")
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage

from .config import config
from .l4_anne import get_anne_player_out
from .l4_help import get_l4d2_core_help
from .l4_request import (
    COMMAND,
    get_all_server_detail,
    get_ip_server,
    get_server_detail,
    reload_ip,
)
from .utils.api.models import OutServer

l4_help = on_command("l4help", aliases={"l4帮助", "l4d2帮助"})
l4_request = on_command("anne", aliases=COMMAND, priority=10)
l4_reload = on_command("l4reload", aliases={"l4刷新,l4重载"})
l4_all = on_command("l4all", aliases={"l4全服"})
l4_connect = on_command("connect", aliases={"l4连接"})
l4_find_player = on_command("l4find", aliases={"l4查找"})


@l4_help.handle()
async def _(matcher: Matcher):
    """帮助"""
    logger.info("开始执行[l4d2帮助]")
    im = await get_l4d2_core_help()
    if isinstance(im, str):
        await matcher.finish(im)
    await UniMessage.image(raw=im).send()


@l4_request.handle()
async def _(
    start: str = CommandStart(),
    command: str = RawCommand(),
    args: Message = CommandArg(),
):
    """例：
    指令：  /橘5
    start: /(command开头指令)
    command: /橘(响应的全部指令)
    args: 5(响应的指令后的数字)
    """

    if start:
        command = command.replace(start, "")
    if command == "anne":
        command = "云"
    _id: Optional[str] = args.extract_plain_text()
    if _id is not None and not _id.isdigit() and _id:
        return
    if not _id:
        _id = None
    logger.info(f"组:{command} ;数字:{_id}")
    msg = await get_server_detail(command, _id)
    if msg is not None:
        if isinstance(msg, str):
            await UniMessage.text(msg).finish()
        if isinstance(msg, bytes):
            await UniMessage.image(raw=msg).finish()
    else:
        await UniMessage.text("服务器无响应").finish()


@l4_find_player.handle()
async def _(
    args: Message = CommandArg(),
):
    msg: str = args.extract_plain_text().strip()
    tag_list: List[str] = msg.split(" ", maxsplit=1)
    if len(tag_list) < 2:
        return await UniMessage.text("格式错误，正确格式：/l4find 组名 玩家名").finish()
    group, name = tag_list
    out: List[OutServer] = await get_server_detail(group, is_img=False)  # type: ignore
    out_msg = "未找到玩家"
    for one in out:
        for player in one["player"]:
            if name in player.name:
                out_msg = await get_ip_server(f"{one['host']}:{one['port']}")

    return await UniMessage.text(out_msg).finish()


@l4_all.handle()
async def _():
    await UniMessage.text(await get_all_server_detail()).finish()


@l4_connect.handle()
async def _(args: Message = CommandArg()):
    ip: Optional[str] = args.extract_plain_text()
    if ip is not None:
        await UniMessage.text(await get_ip_server(ip)).finish()


# anne部分
if config.l4_anne:
    logger.info("加载anne功能")
    from .l4_anne import *  # noqa: F403


@l4_reload.handle()
async def _():
    reload_ip()
    logger.success("重载ip完成")


