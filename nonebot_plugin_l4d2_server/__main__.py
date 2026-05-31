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
from typing import List, Optional, cast

import ujson as json
from nonebot import get_driver
from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command, on_fullmatch
from nonebot_plugin_alconna import UniMessage

from .config import config, config_manager
from .core.help import get_l4d2_core_help
from .message import Gm, Sm
from .server.ban import l4_request
from .server.ban.utils import refresh_server_command_rule
from .server.local import *  # noqa: F403
from .server.query import (
    COMMAND,
    get_all_server_detail,
    get_ip_server,
    get_server_detail,
    reload_ip,
    server_find,
    tj_request,
)
from .shared.utils.api.models import OutServer
from .shared.utils.api.request import L4API, L4D2Api
from .shared.utils.api.utils import out_msg_out
from .shared.utils.group_store import set_group
from .shared.utils.sb_sources import load_pages
from .shared.utils.utils import split_maohao

driver = get_driver()

reload_ip()


l4_help = on_command("l4_help", aliases={"l4help", "l4d2帮助"})

l4_reload_servers = on_command("l4_reload", aliases={"l4reload", "l4刷新", "l4重载"})
l4_list_all_servers = on_command("l4_all", aliases={"l4all", "l4全服"})
l4_connect_server = on_command("l4_connect", aliases={"connect", "l4连接"})
l4_find_player = on_command("l4_find_player", aliases={"l4find", "l4查找"})


config_path = Path(config.l4_path) / "config.json"
refresh_server_command_rule(l4_request)


async def sync_sb_pages_groups() -> None:
    """根据 sb_pages.json 内容刷新所有服务器组"""
    pages = await load_pages()
    if not pages:
        logger.info("sb_pages.json 为空，跳过启动时刷新")
        reload_ip()
        refresh_server_command_rule(l4_request)
        return

    api = L4D2Api()
    ok = 0
    failed: List[str] = []
    for tag, page in pages.items():
        try:
            servers = await api.get_sourceban(tag, page)
            await set_group(tag, servers)
            ok += 1
        except Exception as exc:
            failed.append(f"{tag}: {exc}")

    reload_ip()
    refresh_server_command_rule(l4_request)

    if ok:
        logger.success(f"启动时已刷新 {ok} 个服务器组")
    if failed:
        logger.warning("以下服务器组刷新失败：" + "; ".join(failed))


@driver.on_startup
async def _sync_groups_on_startup() -> None:
    await sync_sb_pages_groups()


@l4_help.handle()
async def handle_l4_help():
    """帮助"""
    logger.info("开始执行[l4d2帮助]")
    im = await get_l4d2_core_help()
    await out_msg_out(im)


@l4_request.handle()
async def handle_server_query(
    start: str = CommandStart(),
    command: str = RawCommand(),
    args: Message = CommandArg(),
):
    logger.info(f"[l4]开始执行请求]：{command}")
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
async def handle_find_player(
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
        out = cast(List[OutServer], await server_find(is_img=False))
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
                        out_msgs = UniMessage.image(raw=out_msg) + UniMessage.text(
                            f"\nconnect {one['host']}:{one['port']}",
                        )
                    elif config.l4_connect and isinstance(out_msg, str):
                        logger.info(f"connect {one['host']}:{one['port']}")
                        out_msgs = UniMessage.text(out_msg) + UniMessage.text(
                            f"\nconnect {one['host']}:{one['port']}",
                        )
                    elif isinstance(out_msg, str):
                        out_msgs = UniMessage.text(out_msg)
                    else:
                        out_msgs = UniMessage.image(raw=out_msg)
                    return await out_msg_out(out_msgs)
        return None
    if len(tag_list) == 2:
        group, name = tag_list
        await UniMessage.text(f"正在查询{group}组").send()
        out = cast(List[OutServer], await server_find(command=group, is_img=True))
        out_msg = Gm.no_player
        for one in out:
            for player in one["player"]:
                if name in player.name:
                    out_msg = await get_ip_server(f"{one['host']}:{one['port']}")
                    logger.info(config.l4_connect)
                    logger.info(type(out_msg))
                    if config.l4_connect and isinstance(out_msg, bytes):
                        logger.info(f"connect {one['host']}:{one['port']}")
                        out_msgs = UniMessage.image(raw=out_msg) + UniMessage.text(
                            f"\nconnect {one['host']}:{one['port']}",
                        )
                    elif config.l4_connect and isinstance(out_msg, str):
                        logger.info(f"connect {one['host']}:{one['port']}")
                        out_msgs = UniMessage.text(out_msg) + UniMessage.text(
                            f"\nconnect {one['host']}:{one['port']}",
                        )
                    elif isinstance(out_msg, str):
                        out_msgs = UniMessage.text(out_msg)
                    else:
                        out_msgs = UniMessage.image(raw=out_msg)

                    return await out_msg_out(out_msgs)
        return None
    return None


@l4_list_all_servers.handle()
async def handle_all_servers():
    await out_msg_out(await get_all_server_detail())


@l4_connect_server.handle()
async def handle_connect_server(args: Message = CommandArg()):
    ip: Optional[str] = args.extract_plain_text()
    if ip is not None:
        host, port = split_maohao(ip)
        await out_msg_out(
            await get_ip_server(ip),
            is_connect=config.l4_connect,
            host=host,
            port=str(port),
        )


@l4_reload_servers.handle()
async def handle_reload_servers(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        with (Path(config.l4_path) / "l4d2.json").open("r", encoding="utf-8") as f:
            content = f.read().strip()
            ip_json = json.loads(content)
        for tag, url in ip_json.items():
            logger.info(f"重载{tag}的ip")
            await L4API.get_sourceban(tag, url)
        reload_ip()
        refresh_server_command_rule(l4_request)
        logger.success("重载ip完成")
        await out_msg_out("重载ip完成")


if "云" in COMMAND:
    ld_tj = on_fullmatch("tj")
    ld_zl = on_fullmatch("zl")
    ld_kl = on_fullmatch("kl")

    @ld_tj.handle()
    async def handle_tj_command(matcher: Matcher):
        await matcher.send("正在寻找牢房信息")
        await matcher.finish(await tj_request("云", "tj"))

    @ld_zl.handle()
    async def handle_zl_command(matcher: Matcher):
        await matcher.send("正在寻找牢房信息")
        await matcher.finish(await tj_request("云", "zl"))

    @ld_kl.handle()
    async def handle_kl_command(matcher: Matcher):
        await matcher.send("正在寻找牢房信息")
        await matcher.finish(await tj_request("云", "kl"))


## 以下为配置修改

l4_toggle_image = on_command(
    "l4_toggle_image",
    aliases={"l4img", "l4图片"},
    permission=SUPERUSER,
)
l4_switch_style = on_command(
    "l4_switch_style",
    aliases={"l4style", "l4风格切换"},
    permission=SUPERUSER,
)


@l4_toggle_image.handle()
async def handle_toggle_image_mode(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    if arg == "开启":
        config_manager.update_image_config(enabled=True)
        await out_msg_out("[l4]已开启图片模式")
    elif arg == "关闭":
        config_manager.update_image_config(enabled=False)
        await out_msg_out("[l4]已关闭图片模式")
    else:
        await UniMessage.text("请在参数后加上开启或关闭").finish()


@l4_switch_style.handle()
async def handle_switch_style():
    if config.l4_style == "default":
        config_manager.update_style_config(style="old")
        await UniMessage.text("[l4]已切换为旧风格").finish()
    else:
        config_manager.update_style_config(style="default")
        await UniMessage.text("[l4]已切换为默认风格").finish()
