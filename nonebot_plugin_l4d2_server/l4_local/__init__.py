from pathlib import Path

from nonebot import on_command
from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_alconna import File, UniMessage, UniMsg

from ..config import config
from ..l4_image.convert import text2pic
from ..utils.utils import mes_list
from .file import change_name, delete_file, updown_l4d2_vpk
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
        try:
            supath = local_path[config.l4_map_index] / "addons"
        except IndexError:
            logger.warning(
                "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
            )
            await UniMessage.text(
                "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
            ).finish()
        vpk_list: list[str] = []
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()

        # 按数字升序，然后按字母和中文排序
        vpk_list.sort(key=sort_key)

        out_msg = "\n".join(
            f"{index + 1}、{line}" for index, line in enumerate(vpk_list)
        )

        img = await text2pic(f"服务器地图:\n{out_msg}")
        await UniMessage.image(raw=img).send()

    @up.handle()
    async def _(matcher: Matcher):
        await matcher.pause("请发送地图文件")

    @up.got("map_url", prompt="图来")
    async def _(ev: Event, msg: UniMsg, matcher: Matcher):
        if not msg.has(File):
            await UniMessage.text("不是文件,退出交互").finish()
        args = ev.model_dump()
        if args["notice_type"] != "offline_file":
            matcher.set_arg("txt", args)  # type: ignore
            return
        l4_file_path = config.l4_local[config.l4_map_index]
        map_path = Path(l4_file_path, "addons")
        # 检查下载路径是否存在
        if not Path(l4_file_path).exists():
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

    @map_change.handle()
    async def _(mathcer: Matcher, args: Message = CommandArg()):
        arg = args.extract_plain_text().strip()
        if arg == "0":
            return
        if not arg:
            await mathcer.pause("请输入修改的地图序号和地图名称，以空格隔开，回复0取消")
        index, new_name = arg.split(" ", maxsplit=1)
        if not index.isdigit():
            await mathcer.pause(
                "请正确输入修改的地图序号和地图名称，以空格隔开，回复0取消",
            )

        vpk_list: list[str] = []
        supath = local_path[config.l4_map_index] / "addons"
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()
        vpk_list.sort(key=sort_key)
        old_path = vpk_list[int(index) - 1]
        r = await change_name(old_path, new_name, supath)
        if r:
            await UniMessage.text("重命名成功").finish()
        await UniMessage.text("重命名失败").finish()

    @map_change.handle()
    async def _(mathcer: Matcher, event: Event):
        arg = event.get_plaintext().strip()
        if arg == "0":
            return
        if not arg:
            await mathcer.finish(
                "请输入修改的地图序号和地图名称，以空格隔开，回复0取消",
            )
        index, new_name = arg.split(" ", maxsplit=1)
        if not index.isdigit():
            await mathcer.finish(
                "请正确输入修改的地图序号和地图名称，以空格隔开，回复0取消",
            )

        vpk_list: list[str] = []
        supath = local_path[config.l4_map_index] / "addons"
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()
        vpk_list.sort(key=sort_key)
        old_path = vpk_list[int(index) - 1]
        r = await change_name(old_path, new_name, supath)
        if r:
            await UniMessage.text("重命名成功").finish()
        await UniMessage.text("重命名失败").finish()

    @map_del.handle()
    async def _(mathcer: Matcher, args: Message = CommandArg()):
        index = args.extract_plain_text().strip()
        print(index)
        if not index.isdigit():
            await mathcer.pause("请输入要删除的地图序号")

        vpk_list: list[str] = []
        supath = local_path[config.l4_map_index] / "addons"
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        vpk_list.sort(key=sort_key)
        old_path = vpk_list[int(index) - 1]
        r = await delete_file(supath / old_path)
        if r:
            await mathcer.finish(f"已删除地图:{old_path}")
        await mathcer.finish("删除失败")

    @map_del.handle()
    async def _(mathcer: Matcher, event: Event):
        index = event.get_plaintext().strip()
        print(index)
        if not index.isdigit():
            await mathcer.finish("请输入正确格式")

        vpk_list: list[str] = []
        supath = local_path[config.l4_map_index] / "addons"
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        vpk_list.sort(key=sort_key)
        old_path = vpk_list[int(index) - 1]
        r = await delete_file(supath / old_path)
        if r:
            await mathcer.finish(f"已删除地图:{old_path}")
        await mathcer.finish("删除失败")
