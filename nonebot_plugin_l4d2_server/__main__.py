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

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import aiofiles
import ujson as json
from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from .config import config
from .l4_help import get_l4d2_core_help
from .l4_local import *  # noqa: F403
from .l4_request import (
    COMMAND,
    get_all_server_detail,
    get_ip_server,
    get_server_detail,
    reload_ip,
    tj_request,
)
from .utils.api.request import L4API

if TYPE_CHECKING:
    from .utils.api.models import OutServer

reload_ip()

l4_help = on_command("l4help", aliases={"l4d2帮助"})
l4_request = on_command("anne", aliases=COMMAND, priority=10)
l4_reload = on_command("l4reload", aliases={"l4刷新,l4重载"})
l4_all = on_command("l4all", aliases={"l4全服"})
l4_connect = on_command("connect", aliases={"l4连接"})
l4_find_player = on_command("l4find", aliases={"l4查找"})

ld_tj = on_command("tj", aliases={"探监"})
ld_zl = on_command("zl")
ld_kl = on_command("kl")
config_path = Path(config.l4_path) / "config.json"


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
    """
    异步函数，用于处理特定的指令。

    Args:
        start (str, optional): 指令的开头部分，默认为 CommandStart() 返回的值。
        command (str, optional): 完整的指令字符串，默认为 RawCommand() 返回的值。
        args (Message, optional): 指令后的参数，默认为 CommandArg() 返回的值。

    Returns:
        None

    Examples:
        示例指令："/橘5"
        - start: "/" (指令的开头部分)
        - command: "/橘" (完整的指令字符串)
        - args: "5" (指令后的参数)

    Notes:
        1. 如果 start 存在，会将 command 中的 start 部分替换为空字符串。
        2. 如果 command 等于 "anne"，则将其替换为 "云"。
        3. 提取 args 中的纯文本内容，如果内容非空且不是数字，则返回。
        4. 如果 args 为空，则将其设置为 None。
        5. 使用 logger 记录处理过程中的信息。
        6. 调用 get_server_detail 函数获取服务器详情，并根据返回结果发送相应的消息。
        7. 如果 get_server_detail 返回 None，则发送 "服务器无响应" 的文本消息。
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


async def _(args: Message = CommandArg()) -> None:
    msg: str = args.extract_plain_text().strip()
    tag_list: List[str] = msg.split(" ", maxsplit=1)
    out_msg: str = "未找到玩家"

    try:
        if len(tag_list) == 1:
            await UniMessage.text("未设置组，正在全服查找，时间较长").send()
            name = tag_list[0]
            out: List["OutServer"] = await get_server_detail(is_img=False)
        else:
            group, name = tag_list
            await UniMessage.text(f"正在查询{group}组").send()
            out = await get_server_detail(group, is_img=False)

        for one in out:
            for player in one["player"]:
                if name in player.name:
                    out_msg = await get_ip_server(f"{one['host']}:{one['port']}")
                    break

    except Exception as e:
        logger.error(f"查找玩家失败: {e}")
        out_msg = "查询失败，请稍后再试"

    await UniMessage.text(out_msg).finish()


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
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    print(arg)
    if not arg:
        reload_ip()
        logger.success("重载ip完成")
        with (Path(config.l4_path) / "config.json").open("r", encoding="utf-8") as f:
            content = f.read().strip()
            ip_json = json.loads(content)
        for tag, url in ip_json.items():
            logger.info(f"重载{tag}的ip")
            await L4API.get_sourceban(tag, url)
        await UniMessage.text("重载ip完成").finish()


l4_add_ban = on_command("l4addban", aliases={"l4添加ban"})


@l4_add_ban.handle()
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().split(" ")

    if len(arg) != 2:
        await UniMessage.text("请在命令后增加响应指令名和网址").finish()

    if not config_path.is_file():
        config_data = {}
    else:
        try:
            with config_path.open("r") as f:
                config_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            config_data = {}

    config_data.update({arg[0]: arg[1]})

    try:
        with config_path.open("w") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        await UniMessage.text(f"文件写入失败: {e}").finish()

    await L4API.get_sourceban(arg[0], arg[1])
    await UniMessage.text(f"添加成功\n组名: {arg[0]}\n网址: {arg[1]}").finish()


l4_del_ban = on_command("l4delban", aliases={"l4删除ban", "l4移除ban"})


@l4_del_ban.handle()
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().split(" ")
    if len(arg) not in [1, 2]:
        await UniMessage.text("请在命令后增加响应指令名或者带响应网址").finish()
    elif len(arg) == 1:
        if not Path(Path(config.l4_path) / "config.json").is_file():
            await UniMessage.text("没有添加过组名").finish()
        else:
            with (Path(config.l4_path) / "config.json").open(
                "r",
                encoding="utf-8",
            ) as f:
                content = f.read().strip()
                config_data = json.loads(content)
            if arg[0] not in config_data:
                await UniMessage.text("没有添加过这个组").finish()
            else:
                del config_data[arg[0]]
            async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            await UniMessage.text(f"删除成功，组名:{arg[0]}").finish()
    elif len(arg) == 2:
        if not Path(Path(config.l4_path) / "config.json").is_file():
            await UniMessage.text("没有添加过组名").finish()
        else:
            with (Path(config.l4_path) / "config.json").open(
                "r",
                encoding="utf-8",
            ) as f:
                content = f.read().strip()
                config_datas = json.loads(content)
            if arg[0] not in config_datas:
                await UniMessage.text("没有添加过这个组").finish()
            else:
                config_datas[arg[0]] = arg[1]
                async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_datas, f, ensure_ascii=False, indent=4)
                await UniMessage.text(f"修改成功，组名:{arg[0]},网址:{arg[1]}").finish()


@ld_tj.handle()
async def _(matcher: Matcher):
    await matcher.send("正在寻找牢房信息")
    await matcher.finish(await tj_request("云", "tj"))


@ld_zl.handle()
async def _(matcher: Matcher):
    await matcher.send("正在寻找牢房信息")
    await matcher.finish(await tj_request("云", "zl"))
