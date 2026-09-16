"""单服 CRUD 命令：替代手工编辑 JSON 文件。

所有指令 SUPERUSER 权限。
"""

from __future__ import annotations

from typing import Optional

from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from ..api import L4API
from ..http_helpers import split_maohao

l4_add_server = on_command(
    "l4添加服务器",
    aliases={"l4_add_server", "l4addserver"},
    permission=SUPERUSER,
)
l4_del_server = on_command(
    "l4删除服务器",
    aliases={"l4_del_server", "l4delserver", "l4deleteserver"},
    permission=SUPERUSER,
)
l4_edit_server = on_command(
    "l4修改服务器",
    aliases={"l4_edit_server", "l4editserver"},
    permission=SUPERUSER,
)
l4_show_group = on_command(
    "l4查看组",
    aliases={"l4showgroup", "l4_list_servers", "l4列服务器"},
    permission=SUPERUSER,
)


def _parse_args(text: str, min_parts: int) -> Optional[list[str]]:
    parts = text.split()
    if len(parts) < min_parts:
        return None
    return parts


@l4_add_server.handle()
async def _(args: Message = CommandArg()) -> None:
    parts = _parse_args(args.extract_plain_text().strip(), min_parts=2)
    if parts is None:
        await UniMessage.text("用法：l4添加服务器 <组名> host:port").finish()
    tag, ip = parts[0], parts[1]
    if split_maohao(ip)[1] == -1:
        await UniMessage.text(f"无效的 ip：{ip}").finish()
    from ..registry import registry

    entry = await registry.add_server(tag, ip)
    from ..commands.query import refresh_server_command_rule

    refresh_server_command_rule()
    await UniMessage.text(
        f"✅ 已添加 {tag}{entry.get('id')} = {entry.get('ip')}",
    ).finish()


@l4_del_server.handle()
async def _(args: Message = CommandArg()) -> None:
    parts = _parse_args(args.extract_plain_text().strip(), min_parts=2)
    if parts is None:
        await UniMessage.text("用法：l4删除服务器 <组名> <id或ip>").finish()
    tag, identifier = parts[0], parts[1]
    from ..registry import registry

    ok = await registry.remove_server(tag, identifier)
    if not ok:
        await UniMessage.text(
            f"未找到 {tag} 中的 {identifier}（id 或 ip）",
        ).finish()
    from ..commands.query import refresh_server_command_rule

    refresh_server_command_rule()
    await UniMessage.text(f"✅ 已删除 {tag} 中的 {identifier}").finish()


@l4_edit_server.handle()
async def _(args: Message = CommandArg()) -> None:
    parts = _parse_args(args.extract_plain_text().strip(), min_parts=3)
    if parts is None:
        await UniMessage.text("用法：l4修改服务器 <组名> <id或ip> <新ip>").finish()
    tag, identifier, new_ip = parts[0], parts[1], parts[2]
    if split_maohao(new_ip)[1] == -1:
        await UniMessage.text(f"无效的新 ip：{new_ip}").finish()
    from ..registry import registry

    entry = await registry.update_server(tag, identifier, new_ip)
    if entry is None:
        await UniMessage.text(
            f"未找到 {tag} 中的 {identifier}",
        ).finish()
    from ..commands.query import refresh_server_command_rule

    refresh_server_command_rule()
    await UniMessage.text(
        f"✅ 已修改 {tag}{entry.get('id')} → {entry.get('ip')}",
    ).finish()


@l4_show_group.handle()
async def _(args: Message = CommandArg()) -> None:
    """列出某组成员并标注 A2S 在线状态。"""
    text = args.extract_plain_text().strip()
    parts = text.split(maxsplit=1)
    if not parts:
        await UniMessage.text("用法：l4查看组 <组名>").finish()
    tag = parts[0]
    from ..registry import registry

    servers = registry.get(tag)
    if not servers:
        await UniMessage.text(f"组「{tag}」不存在或为空").finish()

    ip_list: list[tuple[str, int]] = []
    for s in servers:
        host = s.get("host") or split_maohao(s.get("ip", ""))[0]
        port = s.get("port") or split_maohao(s.get("ip", ""))[1]
        if host and port and port != -1:
            ip_list.append((host, int(port)))

    results = await L4API.a2s_info_batch(ip_list, want_players=False)
    status_by_idx = {int(getattr(s, "steam_id", -1)): s for s, _ in results}

    lines = [f"组「{tag}」共 {len(servers)} 台："]
    for idx, entry in enumerate(servers):
        info = status_by_idx.get(idx)
        if info is None:
            status = "?"
        elif info.server_name == "服务器无响应":
            status = "离线"
        else:
            status = f"{info.player_count}/{info.max_players}"
        lines.append(
            f"  #{entry.get('id')} {entry.get('ip')}  map={info.map_name if info else '?'}  {status}",
        )
    await UniMessage.text("\n".join(lines)).finish(reply=True)
