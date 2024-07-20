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

from typing import Optional

from nonebot import require
from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.plugin import on_command

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage

from .l4_help import get_l4d2_core_help
from .l4_request import COMMAND, get_ip_server, get_server_detail, reload_ip

l4_help = on_command("l4帮助", aliases={"l4help", "l4d2帮助"})
l4_request = on_command("anne", aliases=COMMAND)
l4_reload = on_command("l4重载", aliases={"l4刷新"})
l4_connect = on_command("connect", aliases={"l4连接"})

@l4_help.handle()
async def _(matcher: Matcher):
    """帮助"""
    logger.info("开始执行[l4d2帮助]")
    im = await get_l4d2_core_help()
    print(type(im))
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
    if not _id:
        _id = None
    logger.info(f"组:{command} ;数字:{_id}")
    msg = await get_server_detail(command, _id)
    if msg is not None:
        if isinstance(msg, str):
            await UniMessage.text(msg).finish()
        await UniMessage.image(raw=msg).finish()
    else:
        await UniMessage.text("没有这个服呢").send()


@l4_connect.handle()
async def _(args: Message = CommandArg()):
    ip: Optional[str] = args.extract_plain_text()
    if ip is not None:
        await UniMessage.text(await get_ip_server(ip)).finish()

@l4_reload.handle()
async def _():
    reload_ip()
    logger.success("重载ip完成")
