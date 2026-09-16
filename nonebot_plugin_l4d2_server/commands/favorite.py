"""收藏 / 订阅指令。

- ``l4收藏 <组> <id>`` — 在群聊触发，自动记住当前群为推送目标
- ``l4取关 <组> <id>`` — 取消本群订阅（仅删本群记录，其他群订阅不受影响）
- ``l4收藏列表`` — 列出本群所有订阅
- ``l4通知目标 <组> <id> <群号>`` — SUPERUSER 修改某条订阅的推送目标
"""

from __future__ import annotations

from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from ..services import favorite as fav
from ..services.errors import L4Error

l4_favorite = on_command(
    "l4收藏",
    aliases={"l4fav", "l4_favorite"},
)
l4_unfavorite = on_command(
    "l4取关",
    aliases={"l4unfav", "l4_unfavorite"},
)
l4_list_favorites = on_command(
    "l4收藏列表",
    aliases={"l4favlist", "l4_list_favorites"},
)
l4_set_notify_target = on_command(
    "l4通知目标",
    aliases={"l4notifytarget", "l4_set_notify_target"},
    permission=SUPERUSER,
)


def _usage(verb: str) -> str:
    return f"用法：{verb} <组名> <id或ip>"


async def _extract_group_id(event: GroupMessageEvent) -> int | None:
    return getattr(event, "group_id", None)


@l4_favorite.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    gid = await _extract_group_id(event)
    if gid is None:
        await UniMessage.text("收藏指令仅支持群聊").finish()
    parts = args.extract_plain_text().strip().split()
    if len(parts) < 2:
        await UniMessage.text(_usage("l4收藏")).finish()
    tag, sid = parts[0], parts[1]
    try:
        item = await fav.add_favorite(tag, sid, int(gid))
    except L4Error as exc:
        await UniMessage.text(str(exc)).finish()
    await UniMessage.text(
        f"✅ 已收藏 {item['tag']}{item['server_id']} ({item['host']}:{item['port']})",
    ).finish(reply=True)


@l4_unfavorite.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    gid = await _extract_group_id(event)
    if gid is None:
        await UniMessage.text("取关指令仅支持群聊").finish()
    parts = args.extract_plain_text().strip().split()
    if len(parts) < 2:
        await UniMessage.text(_usage("l4取关")).finish()
    tag, sid = parts[0], parts[1]
    ok = await fav.remove_favorite(tag, sid, int(gid))
    if not ok:
        await UniMessage.text(
            f"未在本群订阅中找到 {tag} {sid}",
        ).finish()
    await UniMessage.text(
        f"✅ 已取消订阅 {tag} {sid}",
    ).finish(reply=True)


@l4_list_favorites.handle()
async def _(event: GroupMessageEvent) -> None:
    gid = await _extract_group_id(event)
    if gid is None:
        await UniMessage.text("收藏列表指令仅支持群聊").finish()
    items = await fav.list_favorites(int(gid))
    if not items:
        await UniMessage.text("本群暂无订阅").finish(reply=True)
    lines = [f"本群订阅（共 {len(items)}）："]
    for it in items:
        lines.append(
            f"  {it['tag']}{it['server_id']}  "
            f"{it['host']}:{it['port']}  "
            f"({it.get('server_name_snapshot', '')})",
        )
    await UniMessage.text("\n".join(lines)).finish(reply=True)


@l4_set_notify_target.handle()
async def _(args: Message = CommandArg()) -> None:
    parts = args.extract_plain_text().strip().split()
    if len(parts) < 3:
        await UniMessage.text(
            "用法：l4通知目标 <组名> <id或ip> <新群号>",
        ).finish()
    tag, sid, new_gid_str = parts[0], parts[1], parts[2]
    if not new_gid_str.lstrip("-").isdigit():
        await UniMessage.text("群号必须是数字").finish()
    new_gid = int(new_gid_str)
    ok = await fav.update_notify_target(tag, sid, new_gid)
    if not ok:
        await UniMessage.text(f"未找到订阅 {tag} {sid}").finish()
    await UniMessage.text(
        f"✅ {tag}{sid} 推送目标已改为 {new_gid}",
    ).finish()
