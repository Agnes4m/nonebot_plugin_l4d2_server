# nonebot_plugin_l4d2_server/commands/server_groups.py
from __future__ import annotations

import ujson as json
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage

from ..utils.api.request import L4D2Api
from ..utils.group_store import (
    export_all,
    get_group,
    list_groups,
    remove_group,
    set_group,
)
from ..utils.sb_sources import del_page, get_page, load_pages, set_page
from ..l4_request import reload_ip
from ..__main__ import refresh_server_command_rule


async def _delete_group_and_page(tag: str) -> tuple[bool, bool]:
    """删除服务器组文件及对应的 URL 配置"""
    group_deleted = await remove_group(tag)
    page_deleted = await del_page(tag)
    return group_deleted, page_deleted

# l4addban <组名> [SourceBans服务器页URL]
l4_add_ban = on_command("l4addban", aliases={"l4添加服务器组"})


@l4_add_ban.handle()
async def _(args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await UniMessage.text("用法：l4addban <组名> [SourceBans服务器页URL]").finish()

    parts = text.split(None, 1)
    tag = parts[0]
    url = parts[1] if len(parts) > 1 else None

    # 如果本次传了 URL，则记入 data/L4D2/sb_pages.json
    if url:
        await set_page(tag, url)

    page = url or await get_page(tag)
    if not page:
        await UniMessage.text(
            f"未在 data/L4D2/sb_pages.json 找到组“{tag}”的 URL；请执行：l4addban {tag} <URL>",
        ).finish()

    api = L4D2Api()
    try:
        server_list = await api.get_sourceban(tag, page)
    except Exception as e:
        await UniMessage.text(f"抓取失败：{e}").finish()

    path = await set_group(tag, server_list)
    await UniMessage.text(
        f"✅ 已更新：{path.name}（共 {len(server_list)} 台）"
    ).finish()


# 批量刷新：遍历 sb_pages.json 中所有组
l4_reload_sb = on_command("l4reloadsb", aliases={"l4刷新服务器组"})


@l4_reload_sb.handle()
async def _():
    pages = await load_pages()
    if not pages:
        await UniMessage.text(
            "data/L4D2/sb_pages.json 为空，先用：l4addban <组名> <URL>"
        ).finish()

    api = L4D2Api()
    ok, fail = 0, []
    for tag, page in pages.items():
        try:
            servers = await api.get_sourceban(tag, page)
            await set_group(tag, servers)
            ok += 1
        except Exception as e:
            fail.append(f"{tag}: {e}")

    msg = [f"✅ 刷新完成：成功 {ok} 个组。"]
    if fail:
        msg.append("❌ 失败：\n" + "\n".join(fail))
    await UniMessage.text("\n".join(msg)).send()
    reload_ip()
    refresh_server_command_rule()


# 列出所有组及数量
l4_list_groups = on_command("l4listgroup", aliases={"l4listgroups", "l4列服务器组"})


@l4_list_groups.handle()
async def _():
    names = await list_groups()
    if not names:
        await UniMessage.text("暂无服务器组。").finish()
    lines = []
    for name in names:
        items = await get_group(name)
        lines.append(f"{name}（{len(items)}）")
    await UniMessage.text("现有服务器组：\n" + "\n".join(lines)).finish()


# 删除服务器组（即删除 data/L4D2/l4d2/<tag>.json）
l4_del_group = on_command("l4delgroup", aliases={"l4删除服务器组"})


@l4_del_group.handle()
async def _(args: Message = CommandArg()):
    tag = args.extract_plain_text().strip()
    if not tag:
        await UniMessage.text("用法：l4delgroup <组名>").finish()
    group_deleted, page_deleted = await _delete_group_and_page(tag)

    if not group_deleted and not page_deleted:
        await UniMessage.text("未找到该组文件或 URL 记录").finish()
        return

    msg_parts = []
    if group_deleted:
        msg_parts.append("服务器组文件")
    if page_deleted:
        msg_parts.append("SourceBans URL")
    await UniMessage.text("✅ 已删除 " + "、".join(msg_parts)).send()
    reload_ip()
    refresh_server_command_rule()


# 删除 sb_pages.json 里的 URL 映射（仅删 URL）
l4_del_page = on_command("l4delpage", aliases={"l4删除服务器页"})


@l4_del_page.handle()
async def _(args: Message = CommandArg()):
    tag = args.extract_plain_text().strip()
    if not tag:
        await UniMessage.text("用法：l4delpage <组名>").finish()
    ok = await del_page(tag)
    await UniMessage.text("✅ 已删除" if ok else "未找到该组的 URL").finish()


# 导出指定组的 JSON 片段（直接读取 data/L4D2/l4d2/<tag>.json）
l4_export_group = on_command("l4exportgroup", aliases={"l4导出服务器组"})


@l4_export_group.handle()
async def _(args: Message = CommandArg()):
    tag = args.extract_plain_text().strip()
    if not tag:
        await UniMessage.text("用法：l4exportgroup <组名>").finish()
    items = await get_group(tag)
    if not items:
        await UniMessage.text("未找到该组。").finish()
    data = {tag: items}
    await UniMessage.text(json.dumps(data, ensure_ascii=False, indent=4)).finish()


# 导出全部组（仅用于查看，组合成一个对象返回，不写入任何聚合文件）
l4_export_groups = on_command("l4exportgroups", aliases={"l4导出全部服务器组"})


@l4_export_groups.handle()
async def _():
    data = await export_all()
    if not data:
        await UniMessage.text("暂无服务器组。").finish()
    await UniMessage.text(json.dumps(data, ensure_ascii=False, indent=4)).finish()
