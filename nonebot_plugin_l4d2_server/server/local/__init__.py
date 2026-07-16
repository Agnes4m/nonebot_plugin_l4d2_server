from pathlib import Path

import aiofiles
from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import File, UniMessage
from nonebot_plugin_waiter import prompt

from ...config import config
from ...presentation.render.convert import text2pic
from ...shared.utils.api.models import WorksopInfo
from ...shared.utils.utils import mes_list, url_to_byte
from .download import process_ws_download, render_workshop_info
from .file import change_name, delete_file, updown_l4d2_vpk
from .utils import (
    get_local_path,
    get_vpk_files,
    process_map_change_or_delete,
    validate_local_path,
)

if not config.l4_local:
    logger.warning(
        "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
    )
else:
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
    async def _():
        if not validate_local_path():
            await UniMessage.text(
                "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
            ).finish()

        vpk_list = get_vpk_files(config.l4_map_index)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()

        out_msg = "\n".join(
            f"{index + 1}、{line}" for index, line in enumerate(vpk_list)
        )
        img = await text2pic(f"服务器地图:\n{out_msg}")
        await UniMessage.image(raw=img).send()

    @l4_map_upload.handle()
    async def handle_map_upload():
        if not validate_local_path():
            await UniMessage.text(
                "未配置有效的本地服务器路径",
            ).finish()

        msg = await prompt("请发送地图文件或下载链接", timeout=120)
        if msg is None:
            await UniMessage.text("操作已超时，已取消").finish()

        # 提取文件 URL 和名称
        files = msg.get(File)
        if files:
            url = files[0].url
            name = files[0].name
        elif text := msg.extract_plain_text().strip():
            if text.startswith(("http://", "https://")):
                url = text
                name = url.split("/")[-1]
            else:
                await UniMessage.text("请输入有效的下载链接").finish()
        else:
            await UniMessage.text("请发送文件或下载链接").finish()

        # 修正：使用与 l4_map 查询/删除一致的路径
        try:
            map_path = get_local_path()[config.l4_map_index] / "addons"
        except IndexError:
            await UniMessage.text("未配置有效的本地服务器路径").finish()

        if not map_path.exists():
            await UniMessage.text("这个路径并不是求生服务器的路径,请检查").finish()

        await l4_map_upload.send("已收到文件,开始下载")
        vpk_files = await updown_l4d2_vpk(map_path, name, url)

        if vpk_files:
            mes = "解压成功,新增以下几个vpk文件"
            await UniMessage.text(mes_list(mes, vpk_files)).finish()
        else:
            await UniMessage.text("你可能上传了相同的文件,或者解压失败了").finish()

    @l4_map_change.handle()
    async def handle_map_change(
        matcher: Matcher,
        event: Event,
        args: Message = CommandArg(),
    ):
        arg = args.extract_plain_text() or event.get_plaintext()
        result = await process_map_change_or_delete(matcher, arg)
        if not result:
            return

        index, new_name = result
        vpk_list = get_vpk_files(config.l4_map_index)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()

        try:
            old_path = vpk_list[index - 1]
            supath = get_local_path()[config.l4_map_index] / "addons"
            success = await change_name(old_path, new_name, supath)
        except IndexError:
            await UniMessage.text("输入的地图序号无效").finish()
        except Exception as e:
            logger.error(f"重命名地图失败: {e}")
            await UniMessage.text("重命名失败").finish()

        await UniMessage.text("重命名成功" if success else "重命名失败").finish()

    @l4_map_delete.handle()
    async def handle_map_del(
        matcher: Matcher,
        event: Event,
        args: Message = CommandArg(),
    ):
        arg = args.extract_plain_text() or event.get_plaintext()
        result = await process_map_change_or_delete(matcher, arg, is_delete=True)
        if not result:
            return

        index, _ = result
        vpk_list = get_vpk_files(config.l4_map_index)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()

        try:
            old_path = vpk_list[index - 1]
            supath = get_local_path()[config.l4_map_index] / "addons"
            success = await delete_file(supath / old_path)
        except IndexError:
            await UniMessage.text("输入的地图序号无效").finish()
        except Exception as e:
            logger.error(f"删除地图失败: {e}")
            await UniMessage.text("删除失败").finish()

        await UniMessage.text(
            f"已删除地图:{old_path}" if success else "删除失败",
        ).finish()


ws_download = on_command(
    "l4创意工坊",
    priority=20,
    permission=config.l4_permission_set,
    block=True,
)


@ws_download.handle()
async def handle_ws_download(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        arg = await prompt("请输入创意工坊id或者url", timeout=60)
        if arg is None:
            await UniMessage.text("操作已超时，已取消").finish()
        arg = arg.extract_plain_text().strip()

    ws_id = await process_ws_download(arg)
    ws_msg = await render_workshop_info(ws_id)

    confirm = await prompt("是否下载该地图？(是/否)", timeout=60)
    if confirm is None or confirm.extract_plain_text().strip() != "是":
        await UniMessage.text("已取消下载").finish()

    # 确定下载路径
    local_paths = get_local_path()
    if local_paths:
        dl_path = local_paths[config.l4_map_index] / "addons"
    else:
        dl_path = Path(config.l4_path) / "addons"

    dl_path.mkdir(parents=True, exist_ok=True)
    ws_msg: WorksopInfo = ws_msg
    filename = ws_msg["filename"]
    final_path = dl_path / filename

    if final_path.is_file():
        logger.info(f"地图文件已存在: {final_path}")
        await UniMessage.text(f"地图已存在: {filename}").finish()

    dl_data = await url_to_byte(ws_msg["file_url"])
    if dl_data is None:
        logger.error(f"下载失败: {ws_msg['file_url']}")
        await UniMessage.text("下载失败").finish()

    async with aiofiles.open(final_path, "wb") as f:
        await f.write(dl_data)

    logger.info(f"地图下载完成: {final_path}")
    await UniMessage.text(f"✅ 地图下载完成: {filename}").send()
    await UniMessage.file(path=final_path, name=f"{ws_msg['title']}.vpk").send()
