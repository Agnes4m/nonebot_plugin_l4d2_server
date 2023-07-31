import asyncio
import re
from time import sleep
from typing import Dict, List, Tuple, Type

from nonebot import on_command, on_keyword, on_notice, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand

from ..l4d2_anne.server import group_key, server_key
from ..l4d2_queries import get_group_ip_to_msg
from ..l4d2_queries.local_ip import ALL_HOST
from ..l4d2_queries.qqgroup import get_tan_jian, qq_ip_queries_pic, split_maohao
from ..l4d2_queries.utils import get_anne_server_ip, json_server_to_tag_dict
from .config import MASTER, driver, l4_config
from .rule import wenjian
from .utils import str_to_picstr

help_ = on_command("l4_help", aliases={"求生帮助"}, priority=20, block=True)


up = on_notice(rule=wenjian)


rename_vpk = on_regex(
    r"^求生地图\s*(\S+.*?)\s*(改|改名)?\s*(\S+.*?)\s*$",
    flags=re.S,
    block=True,
    priority=20,
    permission=MASTER,
)

find_vpk = on_command("l4_map", aliases={"求生地图"}, priority=25, block=True)
del_vpk = on_command(
    "l4_del_map",
    aliases={"求生地图删除", "地图删除"},
    priority=20,
    permission=MASTER,
)
rcon_to_server = on_command(
    "rcon",
    aliases={"求生服务器指令", "服务器指令"},
    permission=MASTER,
)  # noqa: E501
check_path = on_command(
    "l4_check",
    aliases={"求生路径"},
    priority=20,
    block=True,
    permission=MASTER,
)
smx_file = on_command(
    "l4_smx",
    aliases={"求生插件"},
    priority=20,
    block=True,
    permission=MASTER,
)

# anne
anne_player = on_command("Ranne", aliases={"求生anne"}, priority=25, block=True)
anne_bind = on_command(
    "Rbind",
    aliases={"steam绑定", "求生绑定", "anne绑定"},
    priority=20,
    block=True,
)
del_bind = on_command(
    "del_bind",
    aliases={"steam解绑", "求生解绑", "anne解绑"},
    priority=20,
    block=True,
)
prison = on_command("zl", aliases={"坐牢"}, priority=20, block=True)
open_prison = on_command("kl", aliases={"开牢"}, priority=20, block=True)

updata = on_command(
    "updata_anne",
    aliases={"求生更新anne"},
    priority=20,
    block=True,
    permission=MASTER,
)
tan_jian = on_command("tj", aliases={"探监"}, priority=20, block=True)

# 查询
queries_comm = on_keyword(
    keywords={"queries", "求生ip", "求生IP", "connect"},
    priority=20,
    block=True,
)
add_queries = on_command(
    "addq",
    aliases={"求生添加订阅"},
    priority=20,
    block=True,
    permission=MASTER,
)
del_queries = on_command(
    "delq",
    aliases={"求生取消订阅"},
    priority=20,
    block=True,
    permission=MASTER,
)
show_queries = on_command("showq", aliases={"求生订阅"}, priority=20, block=True)
join_server = on_command("ld_jr", aliases={"求生加入"}, priority=20, block=True)
connect_rcon = on_command(
    "Rrcon",
    aliases={"求生连接", "求生链接", "求生rcon"},
    priority=50,
    block=False,
)
end_connect = ["stop", "结束", "连接结束", "结束连接"]
search_api = on_command(
    "search",
    aliases={"求生三方"},
    priority=20,
    block=True,
    permission=MASTER,
)
# which_map = on_keyword("是什么图"), priority=20, block=False)
reload_ip = on_command("l4_reload", aliases={"重载ip"}, priority=30, permission=MASTER)

# 下载内容
up_workshop = on_command(
    "workshop",
    aliases={"创意工坊下载", "求生创意工坊"},
    priority=20,
    block=True,
)
vtf_make = on_command("vtf_make", aliases={"求生喷漆"}, priority=20, block=True)


matchers: Dict[str, List[Type[Matcher]]] = {}


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
        if not push_msg:
            return
        if isinstance(push_msg, Message):
            logger.info("构造")
            try:
                await matcher.finish(push_msg)
            except Exception as E:
                logger.warning(E)
                return
        elif isinstance(push_msg, bytes):
            logger.info("直接发送图片")
            send_msg = MessageSegment.image(push_msg)
        elif msg and type(push_msg) == list:
            logger.info("更加构造函数")
            send_msg = Message(MessageSegment.image(push_msg[0]) + push_msg[-1])
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

        return img if img else "服务器无响应"

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
        return await get_anne_server_ip(ip)
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
            send_msg = MessageSegment.image(push_msg)
        elif msg and type(push_msg) == list:
            send_msg = Message(MessageSegment.image(push_msg[0]) + push_msg[-1])
        elif msg and isinstance(push_msg, str):
            await str_to_picstr(push_msg, matcher)
            return
        else:
            return
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
