from pathlib import Path

from nonebot.adapters import Event
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot_plugin_alconna import File, UniMessage, UniMsg, on_alconna

from ..config import config
from ..l4_image.convert import text2pic
from ..utils.utils import mes_list
from .file import updown_l4d2_vpk
from .utils import sort_key

local_path_list = config.l4_local
if not local_path_list:
    logger.warning(
        "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
    )
else:
    local_path: list[Path] = []
    for folder_path in local_path_list:
        path = Path(folder_path)

        if path.is_dir():
            for nextdir in path.iterdir():
                # 如果找到了名为left4dead2的目录,返回True
                if nextdir.name == "left4dead2" and nextdir.is_dir():
                    local_path.append(nextdir)
            continue
    logger.debug(f"本地服务器路径列表:{local_path}")

    search_map = on_alconna(
        "l4map",
        aliases={"l4地图查询", "l4地图"},
        priority=20,
        block=True,
    )
    up = on_alconna(
        "l4upload",
        aliases={"l4地图上传"},
        priority=5,
        block=True,
    )

    @search_map.handle()
    async def search_map_handler() -> None:
        try:
            if not local_path or config.l4_map_index is None:
                await UniMessage.text("未知错误").finish()
            addons_path = local_path[config.l4_map_index] / "addons"
        except IndexError:
            logger.warning("未配置本地服务器路径")
            await UniMessage.text("未配置本地服务器路径").finish()
            return

        vpk_files: list[str] = []
        if addons_path.is_dir():
            for file in addons_path.iterdir():
                if file.is_file() and file.suffix == ".vpk":
                    vpk_files.append(file.name)

        if not vpk_files:
            await UniMessage.text("未找到可用的VPK文件").finish()
            return

        vpk_files.sort(key=sort_key)
        out_msg = "\n".join(f"{i+1}、{name}" for i, name in enumerate(vpk_files))

        img = await text2pic(f"服务器地图:\n{out_msg}")
        await UniMessage.image(raw=img).send()

    @up.handle()
    async def _():
        await UniMessage.text("请发送地图文件").finish()

    @up.got("map_url", prompt="图来")
    async def handle_upload(
        ev: Event,
        msg: UniMsg,
        matcher: Matcher,
    ) -> None:
        if not msg.has(File):
            await UniMessage.text("不是文件，退出交互").finish()

        args = ev.model_dump()
        if args.get("notice_type") != "offline_file":
            matcher.set_arg("txt", args)  # type: ignore
            return

        try:
            if not hasattr(config, "l4_map_index"):
                await UniMessage.text("未知错误").finish()
            l4_file_path = config.l4_local[config.l4_map_index]
        except (IndexError, AttributeError):
            await UniMessage.text("服务器配置错误").finish()

        map_path = Path(l4_file_path) / "addons"

        if not map_path.parent.exists():
            await UniMessage.text("配置的路径不存在").finish()
        if not map_path.exists():
            await UniMessage.text("无效的求生服务器路径").finish()

        file_info = args.get("file")
        if not file_info:
            await UniMessage.text("无效的文件信息").finish()

        url = file_info.get("url", "")
        name = file_info.get("name", "")

        if not url or not name or not name.endswith(".vpk"):
            await UniMessage.text("无效的文件格式").finish()

        await up.send("已收到文件，开始下载")
        vpk_files = await updown_l4d2_vpk(map_path, name, url)

        if vpk_files:
            mes = "解压成功，新增以下vpk文件："
            await UniMessage.text(mes_list(mes, vpk_files)).finish()
        else:
            await UniMessage.text("文件已存在或解压失败").finish()
