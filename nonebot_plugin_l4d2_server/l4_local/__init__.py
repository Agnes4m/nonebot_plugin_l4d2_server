from pathlib import Path

from nonebot.adapters import Event
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot_plugin_alconna import File, UniMessage, UniMsg, on_alconna

from ..config import config, map_index
from ..l4_image.convert import text2pic
from ..utils.utils import mes_list
from .file import updown_l4d2_vpk

try:
    vpk_path = config.l4_local[map_index]
except IndexError:
    logger.warning(
        "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
    )
    vpk_path = ""

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

    @search_map.handle()
    async def _():
        supath = local_path[map_index] / "addons"
        vpk_list: list[str] = []
        print(supath)
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()
        out_msg = "\n".join(
            f"{index + 1}、{line}" for index, line in enumerate(vpk_list)
        )

        img = await text2pic(f"服务器地图:\n{out_msg}")
        await UniMessage.image(raw=img).send()

    up = on_alconna(
        "l4upload",
        aliases={"l4地图上传"},
        priority=5,
        block=True,
    )

    @up.handle()
    async def _():
        await UniMessage.text("请发送地图文件").finish()

    @up.got("map_url", prompt="图来")
    async def _(ev: Event, msg: UniMsg, matcher: Matcher):
        if not msg.has(File):
            await UniMessage.text("不是文件,退出交互").finish()
        args = ev.dict()
        if args["notice_type"] != "offline_file":
            matcher.set_arg("txt", args)  # type: ignore
            return
        l4_file_path = config.l4_local[map_index]
        map_path = Path(l4_file_path, vpk_path)  # type: ignore
        # 检查下载路径是否存在
        if not Path(l4_file_path).exists():  # type: ignore
            await UniMessage.text("你填写的路径不存在辣").finish()
        if not Path(map_path).exists():
            await UniMessage.text("这个路径并不是求生服务器的路径,请再看看罢").finish()
        url: str = args["file"]["url"]
        name: str = args["file"]["name"]
        # 如果不符合格式则忽略
        await up.send("已收到文件,开始下载")
        vpk_files = await updown_l4d2_vpk(map_path, name, url)
        if vpk_files:
            mes = "解压成功,新增以下几个vpk文件"
            await UniMessage.text(mes_list(mes, vpk_files)).finish()
        else:
            await UniMessage.text("你可能上传了相同的文件,或者解压失败了捏").finish()
