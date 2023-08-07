from time import sleep
from typing import Dict, List, Tuple

from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, Keyword, RawCommand
from nonebot.plugin.on import on_command, on_keyword
from nonebot_plugin_saa import Image, MessageFactory, Text

from ..l4d2_anne.server import server_key, updata_anne_server
from ..l4d2_queries.local_ip import ALL_HOST
from ..l4d2_queries.qqgroup import get_tan_jian, split_maohao
from ..l4d2_queries.utils import queries_server
from ..l4d2_utils.config import MASTER, driver, l4_config
from ..l4d2_utils.utils import str_to_picstr
from .send_msg import get_ip_to_mes

tan_jian = on_command("tj", aliases={"探监"}, priority=20, block=True)
prison = on_command("zl", aliases={"坐牢"}, priority=20, block=True)
open_prison = on_command("kl", aliases={"开牢"}, priority=20, block=True)


async def get_des_ip():
    """初始化"""
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


updata = on_command(
    "updata_anne",
    aliases={"求生更新anne"},
    priority=20,
    block=True,
    permission=MASTER,
)


@updata.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    """更新"""
    if args:
        # 占位先，除了电信服还有再加
        ...
    anne_ip_dict = await updata_anne_server()
    if not anne_ip_dict:
        await matcher.finish("网络开小差了捏")
    server_number = len(anne_ip_dict["云"])
    await matcher.finish(f"更新成功\n一共更新了{server_number}个电信anne服ip")


# 查询
queries_comm = on_keyword(
    keywords={"queries", "求生ip", "求生IP", "connect"},
    priority=20,
    block=True,
)


@queries_comm.handle()
async def _(matcher: Matcher, event: Event, keyword: str = Keyword()):
    msg = event.get_plaintext()

    if not msg:
        await matcher.finish("ip格式如中括号内【127.0.0.1】【114.51.49.19:1810】")
    ip = msg.split(keyword)[-1].split("\r")[0].split("\n")[0].split(" ")
    one_msg = None
    for one in ip:
        if one and one[-1].isdigit():
            one_msg = one
            break
    if not one_msg:
        await matcher.finish()
    ip_list = split_maohao(one_msg)
    msg = await queries_server(ip_list)
    await str_to_picstr(msg, matcher, keyword)
