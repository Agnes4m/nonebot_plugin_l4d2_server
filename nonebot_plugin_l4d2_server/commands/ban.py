"""SourceBans management commands: add / reload / list / remove / export."""

from __future__ import annotations

import ujson as json
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from ..commands.query import (
    refresh_server_command_rule,
)
from ..services import sourceban
from ..store import groups as groups_store
from ..store import pages as pages_store

l4_add_ban = on_command("l4_add_ban", aliases={"l4addban", "l4添加组", "l4添加ban"})
l4_reload_groups = on_command(
    "l4_reload_groups",
    aliases={"l4reloadsb", "l4刷新组"},
)
l4_list_groups = on_command(
    "l4_list_groups",
    aliases={"l4listgroup", "l4listgroups", "l4列组"},
)
l4_remove_group = on_command(
    "l4_remove_group",
    aliases={"l4delgroup", "l4删除组"},
)
l4_remove_page = on_command(
    "l4_remove_page",
    aliases={"l4delpage", "l4删除页"},
)
l4_export_group = on_command(
    "l4_export_group",
    aliases={"l4exportgroup", "l4导出组"},
)
l4_export_groups = on_command(
    "l4_export_groups",
    aliases={"l4exportgroups", "l4导出全部组"},
)


@l4_add_ban.handle()
async def _(args: Message = CommandArg()) -> None:
    text = args.extract_plain_text().strip()
    if not text:
        await UniMessage.text(
            "用法：l4_add_ban <组名> [SourceBans URL]",
        ).finish()
    parts = text.split(None, 1)
    tag = parts[0]
    url = parts[1] if len(parts) > 1 else None
    if url:
        await pages_store.set_page(tag, url)
    page = url or await pages_store.get_page(tag)
    if not page:
        await UniMessage.text(
            f"未在 sb_pages.json 找到组「{tag}」的 URL；请执行：l4addban {tag} <URL>",
        ).finish()
    servers = await sourceban.refresh_group_from_url(tag, page)
    refresh_server_command_rule()
    await UniMessage.text(
        f"✅ 已更新（{tag}，共 {len(servers)} 台）",
    ).finish()


@l4_reload_groups.handle()
async def _() -> None:
    pages = await pages_store.load_pages()
    if not pages:
        await UniMessage.text(
            "sb_pages.json 为空，先用：l4addban <组名> <URL>",
        ).finish()
    ok, fails = await sourceban.refresh_all_pages()
    refresh_server_command_rule()
    msg_lines = [f"✅ 刷新完成：成功 {ok} 个组。"]
    if fails:
        msg_lines.append("❌ 失败：\n" + "\n".join(fails))
    await UniMessage.text("\n".join(msg_lines)).send()


@l4_list_groups.handle()
async def _() -> None:
    names = await groups_store.list_groups()
    if not names:
        await UniMessage.text("暂无服务器组。").finish()
    lines = []
    for name in names:
        items = await groups_store.get_group(name)
        lines.append(f"{name}（{len(items)}）")
    await UniMessage.text("现有服务器组：\n" + "\n".join(lines)).finish()


@l4_remove_group.handle()
async def _(args: Message = CommandArg()) -> None:
    tag = args.extract_plain_text().strip()
    if not tag:
        await UniMessage.text("用法：l4delgroup <组名>").finish()
    group_deleted = await groups_store.remove_group(tag)
    page_deleted = await pages_store.del_page(tag)
    if not group_deleted and not page_deleted:
        await UniMessage.text("未找到该组文件或 URL 记录").finish()
        return
    parts = []
    if group_deleted:
        parts.append("服务器组文件")
    if page_deleted:
        parts.append("SourceBans URL")
    await UniMessage.text("✅ 已删除 " + "、".join(parts)).send()
    refresh_server_command_rule()


@l4_remove_page.handle()
async def _(args: Message = CommandArg()) -> None:
    tag = args.extract_plain_text().strip()
    if not tag:
        await UniMessage.text("用法：l4delpage <组名>").finish()
    ok = await pages_store.del_page(tag)
    await UniMessage.text("✅ 已删除" if ok else "未找到该组的 URL").finish()


@l4_export_group.handle()
async def _(args: Message = CommandArg()) -> None:
    tag = args.extract_plain_text().strip()
    if not tag:
        await UniMessage.text("用法：l4exportgroup <组名>").finish()
    items = await groups_store.get_group(tag)
    if not items:
        await UniMessage.text("未找到该组。").finish()
    data = {tag: items}
    await UniMessage.text(
        json.dumps(data, ensure_ascii=False, indent=4),
    ).finish()


@l4_export_groups.handle()
async def _() -> None:
    data = await groups_store.export_all()
    if not data:
        await UniMessage.text("暂无服务器组。").finish()
    await UniMessage.text(
        json.dumps(data, ensure_ascii=False, indent=4),
    ).finish()
