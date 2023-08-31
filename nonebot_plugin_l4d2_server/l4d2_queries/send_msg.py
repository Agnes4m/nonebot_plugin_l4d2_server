import asyncio
from typing import Dict, List, Tuple

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, CommandStart, RawCommand
from nonebot_plugin_saa import Image, MessageFactory, Text

from ..l4d2_queries.local_ip import ALL_HOST
from ..l4d2_queries.qqgroup import qq_ip_queries_pic
from ..l4d2_queries.utils import get_anne_server_ip, json_server_to_tag_dict
from ..l4d2_utils.classcal import ServerGroup, ServerStatus
from ..l4d2_utils.utils import split_maohao, str_to_picstr
from .local_ip import Group_All_HOST
from .qqgroup import qq_ip_querie
from .utils import group_key


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


async def get_group_ip_to_msg(command: str, text: str = ""):
    """输出群组ip的dict信息"""
    if not text:
        group_tag_list: List[str] = Group_All_HOST[command]
        group_ip_dict: Dict[str, List[Dict[str, str]]] = {}
        tag = len(group_tag_list) == 0
        for tag, one_group in ALL_HOST.items():
            if tag in group_tag_list or tag:
                group_ip_dict.update({tag: one_group})
                ip_tuple_list: List[Tuple[str, str, int]] = []
                for one_server in one_group:
                    number = one_server["id"]
                    host, port = split_maohao(one_server["ip"])
                    ip_tuple_list.append((number, host, int(port)))
                msg_group_server = await qq_ip_querie(ip_tuple_list)
                return await check_group_msg(msg_group_server)
    return None
    # 还没写完
    #     host, port = split_maohao(one_ip["ip"])
    #     msg_tuple = (one_ip["id"], host, port)
    #     ip_list.append(msg_tuple)
    # img = await qq_ip_queries_pic(ip_list, igr)


async def check_group_msg(
    msg: Dict[str, List[ServerStatus]],
):
    send_msg: Dict[str, ServerGroup] = {}
    if msg:
        for tag, server_group in msg.items():
            # 服务器，服务器玩家数量
            # 当前/总数
            server_info = ServerGroup()
            for one_server in server_group:
                if one_server.name == "null":
                    server_info.server_all_number += 1
                    continue
                server_info.server_all_number += 1
                server_info.server_number += 1
                server_info.server_people += one_server.players
                server_info.server_all_people += one_server.max_players
            send_msg[tag] = server_info
        return send_msg
    return None
