"""Query commands: help, group/server/ip queries, player search."""

from __future__ import annotations

from typing import Optional

from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot.plugin import on_command, on_fullmatch
from nonebot_plugin_alconna import UniMessage

from config import config
from messages import Gm, Sm
from registry import registry
from render import build_help_image
from services import server_query

l4_help = on_command("l4_help", aliases={"l4help", "l4d2帮助"})
l4_list_all_servers = on_command("l4_all", aliases={"l4all", "l4全服"})
l4_connect_server = on_command("l4_connect", aliases={"connect", "l4连接"})
l4_find_player = on_command(
    "l4_find_player", aliases={"l4find", "l4查找"},
)


# anne / <tag> matcher is rebuilt dynamically by `refresh_server_command_rule`.
l4_request = on_command("anne", priority=10)


def refresh_server_command_rule() -> None:
    """Update ``l4_request`` rule so all known group tags are accepted."""
    from nonebot.rule import command as command_rule

    l4_request.rule = command_rule(*registry.commands)


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