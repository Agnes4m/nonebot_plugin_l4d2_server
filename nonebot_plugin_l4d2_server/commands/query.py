"""Query commands: help, group/server/ip queries, player search."""

from __future__ import annotations

from typing import Optional

from nonebot import get_driver
from nonebot.adapters import Message
from nonebot.consts import CMD_ARG_KEY, CMD_KEY, PREFIX_KEY
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.plugin import on_command
from nonebot.typing import T_State
from nonebot_plugin_alconna import UniMessage

from ..config import config
from ..messages import Gm, Sm
from ..registry import registry
from ..render import build_help_image
from ..services import server_query

l4_help = on_command("l4_help", aliases={"l4help", "l4d2帮助"})
l4_list_all_servers = on_command("l4_all", aliases={"l4all", "l4全服"})
l4_connect_server = on_command("l4_connect", aliases={"connect", "l4连接"})
l4_find_player = on_command(
    "l4_find_player",
    aliases={"l4find", "l4查找"},
)


# anne / <tag> matcher is rebuilt dynamically by `refresh_server_command_rule`.
l4_request = on_command("anne", priority=10)


async def _server_command_filter(state: T_State) -> bool:
    """规则层过滤：服务器组指令后只能为空或纯数字。

    比如「云」「云1」「云12」通过；「云云」「云abc」「云1a」拒绝，
    不会进入 ``l4_request`` handler。配合 ``CommandRule`` 一起使用。
    """
    prefix_info = state.get(PREFIX_KEY)
    if not prefix_info:
        return False
    if prefix_info.get(CMD_KEY) is None:
        return False
    cmd_arg = prefix_info.get(CMD_ARG_KEY)
    if cmd_arg is None:
        return True
    arg_text = cmd_arg.extract_plain_text().strip()
    return not arg_text or arg_text.isdigit()


def refresh_server_command_rule() -> None:
    """Update ``l4_request`` rule so all known group tags are accepted.

    不用 ``rule.command()`` 重建：它每次都会把全部前缀重新插入全局 TrieRule，
    对已存在的前缀触发 "Duplicated prefix rule" 告警。这里改为幂等写入前缀
    树（同键覆盖，值相同），再挂 ``CommandRule`` + 数字后缀过滤，行为一致
    且无告警。
    """
    from nonebot.rule import TRIE_VALUE, CommandRule, Rule, TrieRule

    starts = get_driver().config.command_start or {""}
    cmds = [(c,) for c in registry.commands]
    for cmd in cmds:
        for start in starts:
            TrieRule.prefix[f"{start}{cmd[0]}"] = TRIE_VALUE(start, cmd)
    l4_request.rule = Rule(CommandRule(cmds), _server_command_filter)


@l4_help.handle()
async def _help_handler() -> None:
    out = await build_help_image()
    if isinstance(out, bytes):
        await UniMessage.image(raw=out).send()
    else:
        await UniMessage.text(out).send()


@l4_request.handle()
async def _server_query_handler(
    start: str = CommandStart(),
    command: str = RawCommand(),
    args: Message = CommandArg(),
) -> None:
    logger.info(f"[l4]开始执行请求: {command}")
    if start:
        command = command.replace(start, "")
    if command == "anne":
        command = "云"

    raw: Optional[str] = args.extract_plain_text().strip()
    server_id: Optional[str] = raw if raw and raw.isdigit() else None

    if raw and not server_id:
        logger.info(Gm.no_id)
        return

    msg = await server_query.get_server_detail(command, server_id)
    if msg is None:
        await UniMessage.text(Sm.server_outtime).finish()
        return

    logger_info = Gm.outputing_group + (f" {server_id}" if server_id else "")
    logger.info(logger_info, is_connect=config.l4_image)

    if isinstance(msg, bytes):
        await UniMessage.image(raw=msg).send()
    else:
        await UniMessage.text(str(msg)).send()

    if server_id is not None and config.l4_connect:
        endpoint = server_query.find_endpoint(command, server_id)
        if endpoint is not None:
            host, port = endpoint
            await UniMessage.text(f"\nconnect {host}:{port}").send()


@l4_list_all_servers.handle()
async def _all_servers_handler() -> None:
    await UniMessage.text(await server_query.get_all_server_detail()).send()


@l4_connect_server.handle()
async def _connect_handler(args: Message = CommandArg()) -> None:
    ip = args.extract_plain_text()
    if ip:
        out = await server_query.get_ip_server(ip)
        if isinstance(out, bytes):
            await UniMessage.image(raw=out).send()
        else:
            await UniMessage.text(out).send()


@l4_find_player.handle()
async def _find_player_handler(matcher: Matcher, args: Message = CommandArg()) -> None:
    text = args.extract_plain_text().strip()
    if not text:
        await UniMessage.text(Gm.add_name).finish()
        return

    parts = text.split(" ", maxsplit=1)
    if len(parts) == 1:
        name = parts[0]
        target_group = None
    else:
        target_group, name = parts

    groups = registry.group_names if target_group is None else [target_group]
    for group in groups:
        out = await server_query.query_group_servers(group)
        for one in out:
            for player in one["player"]:
                if name in player.name:
                    host, port = one["host"], one["port"]
                    out_msg = await server_query.get_ip_server(f"{host}:{port}")
                    if isinstance(out_msg, bytes):
                        await UniMessage.image(raw=out_msg).send()
                    else:
                        await UniMessage.text(out_msg).send()
                    if config.l4_connect:
                        await UniMessage.text(
                            f"\nconnect {host}:{port}",
                        ).send()
                    await matcher.finish()
    await UniMessage.text(Gm.no_player).finish()
