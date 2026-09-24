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
from ..messages import Gm, Sm, split_message
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


# 「云全」：组名后跟这个字显示全部服务器（默认只显示有人的）。
SHOW_ALL_SUFFIX = "全"


async def _server_command_filter(state: T_State) -> bool:
    """规则层过滤：服务器组指令后只能为空、纯数字或「全」。

    比如「云」「云1」「云12」「云全」通过；「云云」「云abc」「云1a」拒绝，
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
    return not arg_text or arg_text.isdigit() or arg_text == SHOW_ALL_SUFFIX


def refresh_server_command_rule() -> None:
    """Update ``l4_request`` rule so all known group tags are accepted.

    不用 ``rule.command()`` 重建：它每次都会把全部前缀重新插入全局 TrieRule，
    对已存在的前缀触发 "Duplicated prefix rule" 告警。这里改为幂等写入前缀
    树（同键覆盖，值相同），再挂 ``CommandRule`` + 数字后缀过滤，行为一致
    且无告警。

    每次重载服务器组后调用；顺带补注册 tj / zl / kl（「云」组是运行中才
    加进来的情况，不用重启）。
    """
    from nonebot.rule import TRIE_VALUE, CommandRule, Rule, TrieRule

    from .admin import register_picker_handlers

    starts = get_driver().config.command_start or {""}
    cmds = [(c,) for c in registry.commands]
    for cmd in cmds:
        for start in starts:
            TrieRule.prefix[f"{start}{cmd[0]}"] = TRIE_VALUE(start, cmd)
    l4_request.rule = Rule(CommandRule(cmds), _server_command_filter)
    register_picker_handlers()


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
    if raw == SHOW_ALL_SUFFIX:
        await _send_group(command, show_all=True)
        return

    server_id: Optional[str] = raw if raw and raw.isdigit() else None

    if raw and not server_id:
        logger.info(Gm.no_id)
        return

    if server_id is None:
        await _send_group(command)
        return

    msg = await server_query.get_server_detail(
        command,
        server_id,
        is_img=config.l4_image,
    )
    if msg is None:
        await UniMessage.text(Sm.server_outtime).finish()
        return

    logger.info(f"{Gm.outputing_group} {server_id}")

    if isinstance(msg, bytes):
        out = UniMessage.image(raw=msg)
        # 文字模式下 render_server_card 已经带了 connect 行（l4_show_ip），不重复加
        if config.l4_connect:
            endpoint = server_query.find_endpoint(command, server_id)
            if endpoint is not None:
                host, port = endpoint
                out += UniMessage.text(f"\nconnect {host}:{port}")
    else:
        out = UniMessage.text(str(msg))

    await out.send()


async def _send_group(command: str, *, show_all: bool = False) -> None:
    """整组查询：一页一张图逐条发送，某条发送失败不影响后面的页。

    默认只列有人的服务器，``show_all``（「云全」）列全部。
    """
    logger.info(Gm.outputing_group)
    sent = failed = 0
    async for part in server_query.iter_group_output(
        command,
        is_img=config.l4_image,
        show_all=show_all,
    ):
        out = (
            UniMessage.image(raw=part)
            if isinstance(part, bytes)
            else UniMessage.text(part)
        )
        try:
            await out.send()
        except Exception as exc:
            failed += 1
            logger.warning(
                f"[l4] {command} 组查询第 {sent + failed} 条消息发送失败: {exc!r}",
            )
        else:
            sent += 1
    if not sent and not failed:
        await UniMessage.text(f"组「{command}」暂无服务器").finish()
    if failed:
        await UniMessage.text(
            f"⚠️ {command} 有 {failed} 条消息发送失败，可稍后重试，"
            f"或用 {command}<序号> 查单台",
        ).send()


@l4_list_all_servers.handle()
async def _all_servers_handler() -> None:
    text = await server_query.get_all_server_detail()
    for chunk in split_message(text.splitlines()) or [Sm.no_get]:
        await UniMessage.text(chunk).send()


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
