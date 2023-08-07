from typing import List, Union

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Arg, ArgPlainText, CommandArg
from nonebot.typing import T_State
from nonebot_plugin_saa import Image, MessageFactory, Text

from ..l4d2_file.utils import all_zip_to_one
from ..l4d2_image.steam import url_to_byte
from ..l4d2_image.vtfs import img_to_vtf
from ..l4d2_utils.utils import upload_file
from .workshop import workshop_msg

# 下载内容
up_workshop = on_command(
    "workshop",
    aliases={"创意工坊下载", "求生创意工坊"},
    priority=20,
    block=True,
)
vtf_make = on_command("vtf_make", aliases={"求生喷漆"}, priority=20, block=True)


@up_workshop.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    if msg:
        matcher.set_arg("ip", args)


@up_workshop.got("ip", prompt="请输入创意工坊网址或者物品id")
async def _(matcher: Matcher, state: T_State, tag: str = ArgPlainText("ip")):
    # 这一部分注释类型有大问题，反正能跑就不改了
    msg = await workshop_msg(tag)
    if not msg:
        await matcher.finish("没有这个物品捏")
    elif isinstance(msg, dict):
        pic = await url_to_byte(msg["图片地址"])
        if not pic:
            return
        message: str = ""
        for item, value in msg.items():
            if item in ["图片地址", "下载地址", "细节"] or not isinstance(item, str):
                continue
            message += f"{item} : {value}\n"
            message += "如果需要上传，请发送 'yes'"
        state["dic"] = msg
        await MessageFactory([Image(pic), Text(message)]).finish()
    elif isinstance(msg, list):
        lenge = len(msg)
        pic = await url_to_byte(msg[0]["图片地址"])  # type: ignore
        message: str = f"有{lenge}个文件\n"
        ones = []
        for one in msg:
            for item, value in one.items():
                if item in ["图片地址", "下载地址", "细节"]:
                    continue
                message += f"{item}:{value}\n"
            ones.append(one)
        state["dic"] = ones


@up_workshop.got("is_sure")
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent, state: T_State):
    is_sure = str(state["is_sure"])
    if is_sure == "yes":
        data_dict: Union[dict, List[dict]] = state["dic"]
        logger.info("开始上传")
        if isinstance(data_dict, dict):
            data_file = await url_to_byte(data_dict["下载地址"])
            if not data_file:
                return
            file_name = data_dict["名字"] + ".vpk"
            await matcher.send("获取地址成功，尝试上传")
            await upload_file(bot, event, data_file, file_name)
        else:
            data_file_list = []
            for data_one in data_dict:
                data_file = await url_to_byte(data_one["下载地址"])
                data_file_list.append(data_file)
                if not data_file:
                    return
                file_name = data_one["名字"] + ".vpk"
                await all_zip_to_one(data_file_list)
                await upload_file(bot, event, data_file, file_name)
    else:
        await matcher.finish("已取消上传")


@vtf_make.handle()
async def _(matcher: Matcher, state: T_State, args: Message = CommandArg()):
    msg: str = args.extract_plain_text()
    if msg not in ["拉伸", "填充", "覆盖", ""]:
        await matcher.finish("错误的图片处理方式")
    if msg == "":
        msg = "拉伸"
    state["way"] = msg
    logger.info("方式", msg)


@vtf_make.got("image", prompt="请发送喷漆图片")
async def _(bot: Bot, event: GroupMessageEvent, state: T_State, tag=Arg("image")):
    pic_msg: GroupMessageEvent = state["image"][0]
    pic_url = pic_msg.dict()["data"]["url"]
    logger.info(pic_url)
    logger.info(type(pic_url))
    tag = state["way"]
    pic_bytes = await url_to_byte(pic_url)
    if not pic_bytes:
        return
    img_io = await img_to_vtf(pic_bytes, tag)
    img_bytes = img_io.getbuffer()
    usr_id = event.get_user_id()
    file_name: str = str(usr_id) + ".vtf"
    await upload_file(bot, event, img_bytes, file_name)
