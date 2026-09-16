"""Local L4D2 server commands: list / upload / rename / delete VPK maps."""

from __future__ import annotations

import contextlib

from nonebot.adapters import Event, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import on_command
from nonebot_plugin_alconna import File, UniMessage
from nonebot_plugin_waiter import prompt

from ..config import config
from ..messages import Wm
from ..render.images import text2pic
from ..services import local_server as svc_local
from ..services.workshop import (
    WorkshopTaskResult,
    download_many,
    parse_workshop_ids,
)

if not config.l4_local:
    from nonebot.log import logger

    logger.warning(
        "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
    )

search_map = on_command(
    "l4本地地图",
    aliases={"l4_map", "l4map", "l4地图查询"},
    priority=20,
    block=True,
)
l4_map_upload = on_command(
    "l4本地上传",
    aliases={"l4_map_upload", "l4upload"},
    priority=5,
    block=True,
)
l4_map_change = on_command(
    "l4本地改名",
    aliases={"l4_map_change", "l4mapchange"},
    priority=20,
    block=True,
)
l4_map_delete = on_command(
    "l4本地删除",
    aliases={"l4_map_delete", "l4mapdel"},
    priority=20,
    block=True,
)


@search_map.handle()
async def _() -> None:
    if not svc_local.has_local_paths():
        await UniMessage.text(
            "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
        ).finish()
    vpk_list = svc_local.list_vpks(config.l4_map_index)
    if not vpk_list:
        await UniMessage.text("未找到可用的VPK文件").finish()
    lines = "\n".join(f"{i + 1}、{name}" for i, name in enumerate(vpk_list))
    img = await text2pic(f"服务器地图:\n{lines}")
    await UniMessage.image(raw=img).send()


@l4_map_upload.handle()
async def _() -> None:
    if not svc_local.has_local_paths():
        await UniMessage.text("未配置有效的本地服务器路径").finish()
    msg = await prompt("请发送地图文件或下载链接", timeout=120)
    if msg is None:
        await UniMessage.text("操作已超时，已取消").finish()

    files = msg.get(File)
    if files:
        url = files[0].url
        name = files[0].name
    elif text := msg.extract_plain_text().strip():
        if text.startswith(("http://", "https://")):
            url, name = text, text.split("/")[-1]
        else:
            await UniMessage.text("请输入有效的下载链接").finish()
    else:
        await UniMessage.text("请发送文件或下载链接").finish()

    addons = svc_local.addons_dir(config.l4_map_index)
    if addons is None:
        await UniMessage.text("未配置有效的本地服务器路径").finish()
        return

    await l4_map_upload.send("已收到文件,开始下载")
    new_files = await svc_local.download_and_extract(addons, name, url)
    if new_files:
        msg_lines = "解压成功,新增以下几个vpk文件\n" + "\n".join(
            f"{i + 1}、{n}" for i, n in enumerate(new_files)
        )
        await UniMessage.text(msg_lines).finish()
    else:
        await UniMessage.text(
            "你可能上传了相同的文件,或者解压失败了",
        ).finish()


def _parse_change_args(
    matcher: Matcher,
    raw: str,
    *,
    is_delete: bool,
) -> tuple[int, str] | None:
    raw = raw.strip()
    if raw == "0":
        return None
    if not raw:
        prompt_text = (
            "请输入要删除的地图序号"
            if is_delete
            else "请输入修改的地图序号和地图名称，以空格隔开，回复0取消"
        )
        matcher.pause(prompt_text)
        return None
    if is_delete:
        if not raw.isdigit():
            matcher.pause("请输入要删除的地图序号")
        return int(raw), ""
    parts = raw.split(" ", maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit():
        matcher.pause("请正确输入修改的地图序号和地图名称，以空格隔开，回复0取消")
        return None
    return int(parts[0]), parts[1]


@l4_map_change.handle()
async def _(matcher: Matcher, event: Event, args: Message = CommandArg()) -> None:
    arg = args.extract_plain_text() or event.get_plaintext()
    parsed = _parse_change_args(matcher, arg, is_delete=False)
    if not parsed:
        return
    index, new_name = parsed

    addons = svc_local.addons_dir(config.l4_map_index)
    if addons is None:
        await UniMessage.text("未配置有效的本地服务器路径").finish()
        return

    vpk_list = svc_local.list_vpk_files(addons)
    if not vpk_list:
        await UniMessage.text("未找到可用的VPK文件").finish()
        return
    try:
        old = vpk_list[index - 1]
    except IndexError:
        await UniMessage.text("输入的地图序号无效").finish()
        return
    success = await svc_local.rename_vpk(addons, old, new_name)
    await UniMessage.text("重命名成功" if success else "重命名失败").finish()


@l4_map_delete.handle()
async def _(matcher: Matcher, event: Event, args: Message = CommandArg()) -> None:
    arg = args.extract_plain_text() or event.get_plaintext()
    parsed = _parse_change_args(matcher, arg, is_delete=True)
    if not parsed:
        return
    index, _ = parsed

    addons = svc_local.addons_dir(config.l4_map_index)
    if addons is None:
        await UniMessage.text("未配置有效的本地服务器路径").finish()
        return

    vpk_list = svc_local.list_vpk_files(addons)
    if not vpk_list:
        await UniMessage.text("未找到可用的VPK文件").finish()
        return
    try:
        old = vpk_list[index - 1]
    except IndexError:
        await UniMessage.text("输入的地图序号无效").finish()
        return
    success = await svc_local.delete_vpk(addons, old)
    await UniMessage.text(
        f"已删除地图:{old}" if success else "删除失败",
    ).finish()


ws_download = on_command(
    "l4创意工坊",
    priority=20,
    permission=config.l4_permission_set,
    block=True,
)


_STATUS_EMOJI = {
    "ok": "✅",
    "duplicate": "♻️",
    "invalid": "⚠️",
    "download_failed": "❌",
}


@ws_download.handle()
async def _(args: Message = CommandArg()) -> None:
    """批量创意工坊下载。

    用法：
      - 命令后直接跟多个 ID 或 URL，逗号/空格/换行分隔，例如
        ``l4创意工坊 123,456 789`` 或 ``l4创意工坊 https://...id=123 456``
      - 不带参数时走 waiter 提示一次输入
    """
    arg = args.extract_plain_text().strip()
    if not arg:
        arg_msg = await prompt(
            "请输入创意工坊id/url，支持多个（逗号/空格/换行分隔）",
            timeout=60,
        )
        if arg_msg is None:
            await UniMessage.text("操作已超时，已取消").finish()
        arg = arg_msg.extract_plain_text().strip()

    ids = parse_workshop_ids(arg)
    if not ids:
        await UniMessage.text("未解析到任何有效 id").finish()

    await UniMessage.text(
        f"开始下载 {len(ids)} 个地图，并发={config.l4_workshop_concurrency}",
    ).send()

    async def _report(r: WorkshopTaskResult) -> None:
        emoji = _STATUS_EMOJI.get(r.status, "❓")
        title = f" {r.title}" if r.title else ""
        err = f" ({r.error})" if r.error else ""
        await UniMessage.text(f"{emoji} {r.item_id}{title} {r.status}{err}").send()

    results = await download_many(
        ids, config.l4_map_index, on_progress=_report,
    )

    ok = sum(1 for r in results if r.status == "ok")
    duplicate = sum(1 for r in results if r.status == "duplicate")
    failed = sum(1 for r in results if r.status in ("download_failed", "invalid"))

    summary = Wm.workshop_summary.format(
        total=len(results),
        ok=ok,
        duplicate=duplicate,
        failed=failed,
    )
    await UniMessage.text(summary).send()

    # 成功项逐个发送文件
    for r in results:
        if r.status == "ok" and r.path is not None and r.title:
            with contextlib.suppress(Exception):
                await UniMessage.file(path=r.path, name=f"{r.title}.vpk").send()

