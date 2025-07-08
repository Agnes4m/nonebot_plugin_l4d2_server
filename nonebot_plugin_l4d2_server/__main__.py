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
from typing import List, Optional

import aiofiles
import ujson as json
from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from .config import config, config_manager
from .l4_help import get_l4d2_core_help
from .l4_local import *  # noqa: F403
from .l4_request import (
    COMMAND,
    get_all_server_detail,
    get_ip_server,
    get_server_detail,
    reload_ip,
    server_find,
    tj_request,
)
from .message import Gm, Sm
from .utils.api.models import OutServer
from .utils.api.request import L4API
from .utils.api.utils import out_msg_out
from .utils.utils import read_config, split_maohao, write_config

reload_ip()

l4_help = on_command("l4help", aliases={"l4d2帮助"})
l4_request = on_command("anne", aliases=COMMAND, priority=10)
l4_reload = on_command("l4reload", aliases={"l4刷新,l4重载"})
l4_all = on_command("l4all", aliases={"l4全服"})
l4_connect = on_command("connect", aliases={"l4连接"})
l4_find_player = on_command("l4find", aliases={"l4查找"})


config_path = Path(config.l4_path) / "config.json"


@l4_help.handle()
async def _():
    """帮助"""
    logger.info("开始执行[l4d2帮助]")
    im = await get_l4d2_core_help()
    await out_msg_out(im)


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

    _id: Optional[str] = args.extract_plain_text().strip()
    if _id and not _id.isdigit():
        logger.info(Gm.no_id)
        return

    if not _id:
        _id = None
        logger.info(Gm.no_id)
    else:
        logger.info(f"ID: {_id}")

    msg = await get_server_detail(command, _id)
    if msg is None:
        await out_msg_out(Sm.server_outtime)
        return

    logger_info_msg = Gm.outputing_group
    if _id is not None:
        logger_info_msg += f" {_id}"
    logger.info(logger_info_msg, is_connect=config.l4_image)
    await out_msg_out(msg)


@l4_find_player.handle()
async def _(
    args: Message = CommandArg(),
):
    # 以后有时间补img格式
    msg: str = args.extract_plain_text().strip()
    if not msg:
        return UniMessage.text(Gm.add_name)
    tag_list: List[str] = msg.split(" ", maxsplit=1)
    if len(tag_list) == 1:
        await UniMessage.text(Sm.no_group_search).send()
        name = tag_list[0]
        out: List[OutServer] = await server_find(is_img=False)  # type: ignore
        logger.info(out)
        logger.info(type(out))
        out_msg = Sm.no_player
        for one in out:
            logger.info(one)
            for player in one["player"]:
                if name in player.name:
                    out_msg = await get_ip_server(f"{one['host']}:{one['port']}")
                    logger.info(config.l4_connect)
                    logger.info(type(out_msg))
                    if config.l4_connect and isinstance(out_msg, bytes):
                        logger.info(f"connect {one['host']}:{one['port']}")
                        out_msg = UniMessage.image(raw=out_msg) + UniMessage.text(
                            f"\nconnect {one['host']}:{one['port']}",
                        )
                    else:
                        out_msg = UniMessage.text(out_msg)
    if len(tag_list) == 2:
        group, name = tag_list
        await UniMessage.text(f"正在查询{group}组").send()
        out: List[OutServer] = await server_find(command=group, is_img=True)
        out_msg = Gm.no_player
        for one in out:
            for player in one["player"]:
                if name in player.name:
                    out_msg = await get_ip_server(f"{one['host']}:{one['port']}")
                    logger.info(config.l4_connect)
                    logger.info(type(out_msg))
                    if config.l4_connect and isinstance(out_msg, bytes):
                        logger.info(f"connect {one['host']}:{one['port']}")
                        out_msg = UniMessage.image(raw=out_msg) + UniMessage.text(
                            f"\nconnect {one['host']}:{one['port']}",
                        )
                    else:
                        out_msg = UniMessage.text(out_msg)

    return await out_msg_out(out_msg)


@l4_all.handle()
async def _():
    await out_msg_out(await get_all_server_detail())


@l4_connect.handle()
async def _(args: Message = CommandArg()):
    ip: Optional[str] = args.extract_plain_text()
    if ip is not None:
        host, port = split_maohao(ip)
        await out_msg_out(
            await get_ip_server(ip),
            is_connect=config.l4_connect,
            host=host,
            port=port,
        )


@l4_reload.handle()
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        reload_ip()
        logger.success("重载ip完成")
        with (Path(config.l4_path) / "l4d2.json").open("r", encoding="utf-8") as f:
            content = f.read().strip()
            ip_json = json.loads(content)
        for tag, url in ip_json.items():
            logger.info(f"重载{tag}的ip")
            await L4API.get_sourceban(tag, url)
        await out_msg_out("重载ip完成")


l4_add_ban = on_command("l4addban", aliases={"l4添加ban"})


@l4_add_ban.handle()
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().split(" ")
    if len(arg) != 2:
        await UniMessage.text("请在命令后增加响应指令名和网址").finish()

    config_data = read_config(config_path)
    config_data.update({arg[0]: arg[1]})
    write_config(config_path, config_data)

    await L4API.get_sourceban(arg[0], arg[1])
    await UniMessage.text("添加成功\n组名: {arg[0]}\n网址: {arg[1]}").send()


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
            await out_msg_out(f"删除成功，组名:{arg[0]}")
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
                await out_msg_out(f"修改成功，组名:{arg[0]},网址:{arg[1]}")


if "云" in COMMAND:
    ld_tj = on_command("tj", aliases={"探监"})
    ld_zl = on_command("zl")
    ld_kl = on_command("kl")

    @ld_tj.handle()
    async def _(matcher: Matcher):
        await matcher.send("正在寻找牢房信息")
        await matcher.finish(await tj_request("云", "tj"))

    @ld_zl.handle()
    async def _(matcher: Matcher):
        await matcher.send("正在寻找牢房信息")
        await matcher.finish(await tj_request("云", "zl"))

    @ld_kl.handle()
    async def _(matcher: Matcher):
        await matcher.send("正在寻找牢房信息")
        await matcher.finish(await tj_request("云", "kl"))


## 以下为配置修改

img_trung = on_command("l4img", aliases={"l4图片"}, permission=SUPERUSER)
style_trung = on_command("l4style", aliases={"l4风格切换"}, permission=SUPERUSER)


@img_trung.handle()
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    if arg == "开启":
        config_manager.update_image_config(enabled=True)
        await out_msg_out("[l4]已开启图片模式")
    elif arg == "关闭":
        config_manager.update_image_config(enabled=False)
        await out_msg_out("[l4]已关闭图片模式")
    else:
        await UniMessage.text("请在参数后加上开启或关闭").finish()


@style_trung.handle()
async def _():
    if config.l4_style == "default":
        config_manager.update_style_config(style="old")
        await UniMessage.text("[l4]已切换为旧风格").finish()
    else:
        config_manager.update_style_config(style="default")
        await UniMessage.text("[l4]已切换为默认风格").finish()
