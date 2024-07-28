import re
from pathlib import Path
from typing import Tuple

from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Event, Message, NoticeEvent
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg, RegexGroup

# from nonebot.typing import T_State
from ..l4d2_utils.config import MASTER, config_manager, file_format, l4_config, vpk_path
from ..l4d2_utils.rule import wenjian
from ..l4d2_utils.txt_to_img import mode_txt_to_img
from ..l4d2_utils.utils import del_map, get_vpk, mes_list, rename_map
from .input_json import upload  # noqa: F401
from .utils import updown_l4d2_vpk

up = on_command(
    "l4_upload",
    aliases={"l4地图上传"},
    priority=20,
    block=True,
)


rename_vpk = on_regex(
    r"^l4地图\s*(\S+.*?)\s*(改|改名)?\s*(\S+.*?)\s*$",
    flags=re.DOTALL,
    block=True,
    priority=20,
    permission=MASTER,
)

find_vpk = on_command("l4_map", aliases={"l4地图"}, priority=25, block=True)
del_vpk = on_command(
    "l4_del_map",
    aliases={"l4地图删除", "地图删除"},
    priority=20,
    permission=MASTER,
)


check_path = on_command(
    "l4_check",
    aliases={"l4路径"},
    priority=20,
    block=True,
    permission=MASTER,
)
smx_file = on_command(
    "l4_smx",
    aliases={"l4插件"},
    priority=20,
    block=True,
    permission=MASTER,
)


@up.handle()
async def _():
    ...


@up.got("map_url", prompt="图来")
async def _(matcher: Matcher, event: Event):
    if not isinstance(event, NoticeEvent) or not wenjian(event):
        await matcher.finish("未检测到地图")
        return
    args = event.dict()
    if args["notice_type"] != "offline_file":
        matcher.set_arg("txt", args)  # type: ignore
        return
    l4_file_path = l4_config.l4_ipall[l4_config.l4_number]["location"]
    map_path = Path(l4_file_path, vpk_path)  # type: ignore
    # 检查下载路径是否存在
    if not Path(l4_file_path).exists():  # type: ignore
        await matcher.finish("你填写的路径不存在辣")
    if not Path(map_path).exists():
        await matcher.finish("这个路径并不是求生服务器的路径，请再看看罢")
    url: str = args["file"]["url"]
    name: str = args["file"]["name"]
    # 如果不符合格式则忽略
    await up.send("已收到文件，开始下载")
    vpk_files = await updown_l4d2_vpk(map_path, name, url)
    if vpk_files:
        mes = "解压成功，新增以下几个vpk文件"
        await matcher.finish(mes_list(mes, vpk_files))
    else:
        await matcher.finish("你可能上传了相同的文件，或者解压失败了捏")


path_list: str = "请选择上传位置（输入阿拉伯数字)"
times = 0
for one_path in l4_config.l4_ipall:
    times += 1
    path_msg = one_path["location"]
    path_list += f"\n {times!s} | {path_msg}"


@up.got("is_sure", prompt=path_list)
async def _(matcher: Matcher):
    args = matcher.get_arg("txt")
    l4_file = l4_config.l4_ipall
    if args is None:
        await matcher.finish("获取文件出错辣，再试一次吧")
        return

    is_sure = str(matcher.get_arg("is_sure")).strip()
    if not is_sure.isdigit():
        await matcher.finish("已取消上传")

    file_path: str = ""
    for one_server in l4_file:
        if one_server["id_rank"] == is_sure:
            file_path = one_server["location"]
    if not file_path:
        await matcher.finish("没有这个序号拉baka")

    map_path = Path(file_path, vpk_path)

    # 检查下载路径是否存在
    if not Path(file_path).exists():
        await matcher.finish("你填写的路径不存在辣")
    if not map_path.exists():
        await matcher.finish("这个路径并不是求生服务器的路径，请再看看罢")

    url = args["file"]["url"]
    name = args["file"]["name"]
    # 如果不符合格式则忽略
    if not name.endswith(file_format):  # type: ignore
        return

    await matcher.send("已收到文件，开始下载")
    vpk_files = await updown_l4d2_vpk(map_path, name, url)  # type: ignore

    if vpk_files:
        logger.info("检查到新增文件")
        mes = "解压成功，新增以下几个vpk文件"
    elif vpk_files is None:
        await matcher.finish("文件错误")
        return
    else:
        mes = "你可能上传了相同的文件，或者解压失败了捏"

    await matcher.finish(mes_list(mes, vpk_files))


@find_vpk.handle()
async def _():
    map_path = Path(l4_config.l4_ipall[l4_config.l4_number]["location"], vpk_path)
    name_vpk = get_vpk(map_path)
    logger.info("获取文件列表成功")
    mes = "当前服务器下有以下vpk文件"
    msg = mes_list("", name_vpk).replace(" ", "")

    await mode_txt_to_img(mes, msg)


@del_vpk.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    num1 = args.extract_plain_text()
    if num1:
        matcher.set_arg("num", args)


@del_vpk.got("num", prompt="你要删除第几个序号的地图(阿拉伯数字)")
async def _(matcher: Matcher, tag: str = ArgPlainText("num")):
    map_path = Path(l4_config.l4_ipall[l4_config.l4_number]["location"], vpk_path)
    vpk_name = del_map(int(tag), map_path)
    await matcher.finish("已删除地图：" + vpk_name)


@rename_vpk.handle()
async def _(
    matcher: Matcher,
    matched: Tuple[int, str, str] = RegexGroup(),
):
    num, useless, rename = matched
    map_path = Path(l4_config.l4_ipall[l4_config.l4_number]["location"], vpk_path)
    logger.info("检查是否名字是.vpk后缀")
    if not rename.endswith(".vpk"):
        rename = rename + ".vpk"
    logger.info("尝试改名")
    try:
        map_name = rename_map(num, rename, map_path)
        if map_name:
            await matcher.finish("改名成功\n原名:" + map_name + "\n新名称:" + rename)
    except ValueError:
        await matcher.finish("参数错误,输入【求生地图】获取全部名称")


@check_path.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg.startswith("切换"):
        msg_number = int("".join(msg.replace("切换", " ").split()))
        if msg_number > len(l4_config.l4_ipall) or msg_number < 0:
            await matcher.send("没有这个序号的路径呐")
        else:
            l4_config.l4_number = msg_number - 1
            now_path = l4_config.l4_ipall[l4_config.l4_number]["location"]
            await matcher.send(
                f"已经切换路径为\n{l4_config.l4_number + 1!s}、{now_path}",
            )  # noqa: E501
            config_manager.save()
    else:
        now_path = l4_config.l4_ipall[l4_config.l4_number]["location"]
        await matcher.send(f"当前的路径为\n{l4_config.l4_number + 1!s}、{now_path}")


@smx_file.handle()
async def _():
    smx_path = Path(
        l4_config.l4_ipall[l4_config.l4_number]["location"],
        "left4dead2/addons/sourcemod/plugins",
    )
    name_smx = get_vpk(smx_path, file_=".smx")
    logger.info("获取文件列表成功")
    mes = "当前服务器下有以下smx文件"
    msg = ""
    msg = mes_list(msg, name_smx).replace(" ", "")
    await mode_txt_to_img(mes, msg)
