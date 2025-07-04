from pathlib import Path

import aiofiles
from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot_plugin_alconna import File, UniMessage, UniMsg
from nonebot_plugin_waiter import prompt

from ..config import config
from ..l4_image.convert import text2pic
from ..utils.api.models import WorksopInfo
from ..utils.utils import mes_list, url_to_byte
from .download import process_ws_download
from .file import change_name, delete_file, updown_l4d2_vpk
from .utils import (
    get_vpk_files,
    local_path,
    process_map_change_or_delete,
    validate_local_path,
)

local_path_list = config.l4_local
if not local_path_list:
    logger.warning(
        "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
    )
else:

    search_map = on_command(
        "l4map",
        aliases={"l4地图查询", "l4地图"},
        priority=20,
        block=True,
    )
    up = on_command(
        "l4upload",
        aliases={"l4地图上传"},
        priority=5,
        block=True,
    )
    map_change = on_command(
        "l4mapchange",
        aliases={"l4地图修改"},
        priority=20,
        block=True,
    )
    map_del = on_command(
        "l4mapdel",
        aliases={"l4地图删除"},
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

    @up.handle()
    async def _(matcher: Matcher):
        await matcher.pause("请发送地图文件")

    @up.got("map_url", prompt="图来")
    async def handle_up_got(ev: Event, msg: UniMsg):
        if not msg.has(File):
            await UniMessage.text("不是文件,退出交互").finish()

        args = ev.model_dump()
        if args["notice_type"] != "offline_file":
            return

        if not validate_local_path():
            await UniMessage.text("未配置有效的本地服务器路径").finish()

        l4_file_path = config.l4_local[config.l4_map_index]
        map_path = Path(l4_file_path, "addons")

        if not Path(l4_file_path).exists():
            await UniMessage.text("你填写的路径不存在").finish()
        if not Path(map_path).exists():
            await UniMessage.text("这个路径并不是求生服务器的路径,请检查").finish()

        url: str = args["file"]["url"]
        name: str = args["file"]["name"]

        await up.send("已收到文件,开始下载")
        vpk_files = await updown_l4d2_vpk(map_path, name, url)

        if vpk_files:
            mes = "解压成功,新增以下几个vpk文件"
            await UniMessage.text(mes_list(mes, vpk_files)).finish()
        else:
            await UniMessage.text("你可能上传了相同的文件,或者解压失败了").finish()

    @map_change.handle()
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
            supath = local_path[config.l4_map_index] / "addons"
            success = await change_name(old_path, new_name, supath)
        except IndexError:
            await UniMessage.text("输入的地图序号无效").finish()
        except Exception as e:
            logger.error(f"重命名地图失败: {e}")
            await UniMessage.text("重命名失败").finish()

        await UniMessage.text("重命名成功" if success else "重命名失败").finish()

    @map_del.handle()
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
            supath = local_path[config.l4_map_index] / "addons"
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
    "l4ws",
    aliases={"l4工坊下载"},
    priority=20,
    permission=config.l4_permission_set,
    block=True,
)


@ws_download.handle()
async def _(matcher: Matcher, state: T_State, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        arg = await prompt("请输入创意工坊id或者url", timeout=60)
        if arg is None:
            return
        arg = arg.extract_plain_text().strip()

    ws_msg = await process_ws_download(arg)
    state["workshop"] = ws_msg
    await matcher.pause("是否下载")


@ws_download.handle()
async def _(state: T_State, msg: UniMsg):
    if msg.extract_plain_text().strip() == "是":
        try:
            ws_path = Path(config.l4_local[config.l4_map_index]) / "addons"
            cache = True
        except IndexError:
            ws_path = Path(config.l4_path) / "addons"
            cache = False

        try:
            ws_path.mkdir(parents=True, exist_ok=True)
            ws_msg: WorksopInfo = state["workshop"]
            logger.info(
                f"正在下载地图: {ws_msg['title']} (文件名: {ws_msg['filename']})",
            )

            final_path = ws_path / ws_msg["filename"]
            if final_path.is_file():
                logger.info(f"地图文件已存在: {final_path}")
            else:
                dl_msg = await url_to_byte(ws_msg["file_url"])
                if dl_msg is None:
                    logger.error(f"下载失败: {ws_msg['file_url']}")
                    await UniMessage.text("下载失败").finish()

                async with aiofiles.open(final_path, "wb") as f:
                    await f.write(dl_msg)
                logger.info(f"地图下载完成: {final_path}")

            await UniMessage.file(path=final_path, name=f"{ws_msg['title']}.vpk").send()

            if cache:
                final_path.unlink()
                logger.info(f"已清理临时文件: {final_path}")

        except Exception as e:
            logger.error(f"处理地图下载时出错: {e}")
            await UniMessage.text("处理地图时发生错误").finish()
