import asyncio
from time import sleep
from typing import Dict, List, Tuple

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot_plugin_saa import Image, MessageFactory, Text

from ..l4d2_anne.server import group_key, server_key
from ..l4d2_queries.local_ip import ALL_HOST
from ..l4d2_queries.qqgroup import get_tan_jian, qq_ip_queries_pic, split_maohao
from ..l4d2_queries.send_msg import get_group_ip_to_msg
from ..l4d2_queries.utils import get_anne_server_ip, json_server_to_tag_dict
from ..l4d2_utils.config import driver, l4_config
from ..l4d2_utils.utils import str_to_picstr

tan_jian = on_command("tj", aliases={"探监"}, priority=20, block=True)
prison = on_command("zl", aliases={"坐牢"}, priority=20, block=True)
open_prison = on_command("kl", aliases={"开牢"}, priority=20, block=True)


async def get_des_ip():
    """初始化"""
    global ALL_HOST
    global ANNE_IP
    global matchers
    global Group_All_HOST

    def count_ips(ip_dict: Dict[str, List[Dict[str, str]]]):
        """输出加载ip"""
        global ANNE_IP
        for key, value in ip_dict.items():
            if key in ["error_", "success_"]:
                ip_dict.pop(key)
                break
            count = len(value)
            logger.info(f"已加载：{key} | {count}个")
            if key == "云":
                ANNE_IP = {key: value}
        sleep(1)

    count_ips(ALL_HOST)
    ip_anne_list = []
    try:
        for one_tag in l4_config.l4_zl_tag:
            ips = ALL_HOST[one_tag]
            ip_anne_list: List[Tuple[str, str, str]] = []
            for one_ip in ips:
                host, port = split_maohao(one_ip["ip"])
                ip_anne_list.append((one_ip["id"], host, port))
    except (KeyError, TypeError):
        pass
    await get_read_ip(ip_anne_list)

    @tan_jian.handle()
    async def _(matcher: Matcher):
        msg = await get_tan_jian(ip_anne_list, 1)
        await str_to_picstr(push_msg=msg, matcher=matcher)

    @prison.handle()
    async def _(matcher: Matcher):
        msg = await get_tan_jian(ip_anne_list, 2)
        await str_to_picstr(push_msg=msg, matcher=matcher)

    @open_prison.handle()
    async def _(matcher: Matcher):
        msg = await get_tan_jian(ip_anne_list, 3)
        await str_to_picstr(push_msg=msg, matcher=matcher)


async def get_read_ip(ip_anne_list: List[Tuple[str, str, str]]):
    get_ip = on_command("云", aliases=server_key(), priority=50, block=True)
    if not ip_anne_list:
        ...

    @get_ip.handle()
    async def _(
        matcher: Matcher,
        start: str = CommandStart(),
        command: str = RawCommand(),
        args: Message = CommandArg(),
    ):
        if start:
            command = command.replace(start, "")
        if command == "anne":
            command = "云"
        msg: str = args.extract_plain_text()
        push_msg = await get_ip_to_mes(msg, command)
        if push_msg is None:
            return

        if isinstance(push_msg, bytes):
            logger.info("直接发送图片")
            await MessageFactory([Image(push_msg)]).finish()
        elif msg and type(push_msg) == list:
            logger.info("更加构造函数")
            await MessageFactory([Image(push_msg[0]), Text(push_msg[-1])]).finish()
        elif msg and isinstance(push_msg, str):
            send_msg = push_msg
        else:
            logger.info("出错了")
            return
        logger.info(type(send_msg))
        if not send_msg:
            logger.warning("没有")
        await matcher.finish(send_msg)


async def get_ip_to_mes(msg: str, command: str = ""):
    if not msg:
        # 以图片输出全部当前
        igr = False
        # if command in gamemode_list:
        #     this_ips = [
        #         d for l in ALL_HOST.values() for d in l if d.get("version") == command
        #     ]
        #     igr = True
        # else:
        this_ips = ALL_HOST[command]
        ip_list: List[Tuple[str, str, str]] = []
        for one_ip in this_ips:
            host, port = split_maohao(one_ip["ip"])
            msg_tuple = (one_ip["id"], host, port)
            ip_list.append(msg_tuple)
        img = await qq_ip_queries_pic(ip_list, igr)
        return img if img else None

    if not msg[0].isdigit():
        # if any(mode in msg for mode in gamemode_list):
        #     pass
        # else:
        return None
    message = await json_server_to_tag_dict(command, msg)
    if len(message) == 0:
        # 关键词不匹配，忽略
        return None
    ip = str(message["ip"])
    logger.info(ip)

    try:
        msg_send = await get_anne_server_ip(ip)
        if msg_send:
            return msg_send

    except (OSError, asyncio.exceptions.TimeoutError):
        return "服务器无响应"


async def get_read_group_ip():
    """输出群组服务器"""
    get_grou_ip = on_command("anne", aliases=group_key(), priority=80, block=True)

    @get_grou_ip.handle()
    async def _(
        matcher: Matcher,
        start: str = CommandStart(),
        command: str = RawCommand(),
        args: Message = CommandArg(),
    ):
        if start:
            command = command.replace(start, "")
        msg: str = args.extract_plain_text()
        push_msg = await get_group_ip_to_msg(msg, command)
        if isinstance(push_msg, bytes):
            await MessageFactory([Image(push_msg)]).finish()
        elif msg and type(push_msg) == list:
            await MessageFactory([Image(push_msg[0]), Text(push_msg[-1])]).finish()
        elif msg and isinstance(push_msg, str):
            await str_to_picstr(push_msg, matcher)
        await matcher.finish()


# tests = on_command("测试1")

# @tests.handle()
# async def _(event: Event,arg:Message=CommandArg()):
#     logger.info(event)
#     logger.info(arg.extract_plain_text())


async def init():
    global matchers
    # print('启动辣')

    await get_des_ip()


@driver.on_startup
async def _():
    await init()
