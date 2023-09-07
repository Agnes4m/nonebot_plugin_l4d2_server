import json
from time import sleep
from typing import Dict, List, Tuple, Union

from nonebot import on_command, on_keyword
from nonebot.adapters import Event, Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg, CommandStart, Keyword, RawCommand
from nonebot_plugin_saa import Image, MessageFactory, Text

from ..l4d2_anne.server import updata_anne_server
from ..l4d2_image import server_group_ip_pic
from ..l4d2_queries.qqgroup import add_ip, del_ip, get_number_url, show_ip
from ..l4d2_queries.utils import queries_server
from ..l4d2_server.rcon import command_server
from ..l4d2_utils.config import DATA_PATH, MASTER, driver, l4_config
from ..l4d2_utils.txt_to_img import mode_txt_to_img
from ..l4d2_utils.utils import split_maohao, str_to_picstr
from .himi import get_himi_ip
from .local_ip import ALL_HOST
from .qqgroup import get_tan_jian
from .send_msg import get_group_ip_to_msg, get_ip_to_mes
from .utils import server_key

tan_jian = on_command("tj", aliases={"探监"}, priority=20, block=True)
prison = on_command("zl", aliases={"坐牢"}, priority=20, block=True)
open_prison = on_command("kl", aliases={"开牢"}, priority=20, block=True)
rcon_to_server = on_command(
    "rcon",
    aliases={"求生服务器指令", "服务器指令"},
    permission=MASTER,
)

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
add2_queries = on_command(
    "l4add",
    aliases={"l4添加查询", "l4增加查询"},
    priority=20,
    block=True,
    permission=MASTER,
)
del2_queries = on_command(
    "l4del",
    aliases={"l4删除查询", "l4取消查询"},
    priority=20,
    block=True,
    permission=MASTER,
)
show_queries = on_command("showq", aliases={"求生订阅"}, priority=20, block=True)
join_server = on_command("ld_jr", aliases={"求生加入"}, priority=20, block=True)

updata_himi = on_command(
    "update_hime",
    aliases={"公益服更新,l4公益服更新"},
    priority=10,
    block=True,
)


async def get_des_ip():
    """初始化"""

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
        """例：
        指令：  /橘5
        start: /(command开头指令)
        command: /橘(响应的全部指令)
        args: 5(响应的指令后的数字)
        """
        print(start, command, args)
        if start:
            command = command.replace(start, "")
        if command == "anne":
            command = "云"
        msg: str = args.extract_plain_text()
        if "组" in msg:
            logger.info(f"关键词：{command}")
            # 以群组模式输出
            push_msg = await get_group_ip_to_msg(command)
            if push_msg is None or not push_msg:
                await matcher.finish("当前对象里并没有组")
                return
            print(push_msg)
            msg_img = await server_group_ip_pic(push_msg)
            await MessageFactory([Image(msg_img)]).send()
        else:
            push_msg = await get_ip_to_mes(msg, command)
            if push_msg is None:
                return

            if isinstance(push_msg, bytes):
                logger.info("直接发送图片")
                await MessageFactory([Image(push_msg)]).finish()
                return
            if msg and isinstance(push_msg, list):
                logger.info("更加构造函数")
                await MessageFactory([Image(push_msg[0]), Text(push_msg[-1])]).finish()
                return
            if msg and isinstance(push_msg, str):
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


@add_queries.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()):
    msg = args.extract_plain_text()
    if len(msg) == 0:
        await matcher.finish("请在该指令后加入参数，例如【114.51.49.19:1810】")
    [host, port] = split_maohao(msg)
    group_id = event.group_id
    msg = await add_ip(group_id, host, port)
    await matcher.finish(msg)


@del_queries.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    msg = args.extract_plain_text()
    if not msg.isdigit():
        await matcher.finish("请输入正确的序号数字")
    group_id = event.group_id
    msg = await del_ip(group_id, msg)
    await matcher.finish(msg)


@show_queries.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    group_id = event.group_id
    msg = await show_ip(group_id)
    if not msg:
        await matcher.finish("当前没有启动的服务器捏")
        return
    if isinstance(msg, str):
        await matcher.finish(msg)
    else:
        await MessageFactory([Image(msg)]).finish()


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
        return
    ip_list = split_maohao(one_msg)
    msg = await queries_server(ip_list)
    await str_to_picstr(msg, matcher, keyword)


@join_server.handle()
async def _(args: Message = CommandArg()):
    msg = args.extract_plain_text()
    url = await get_number_url(msg)
    await join_server.finish(url)


@rcon_to_server.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    msg = args.extract_plain_text()
    if msg:
        matcher.set_arg("command", args)


@rcon_to_server.got("command", prompt="请输入向服务器发送的指令")
async def _(matcher: Matcher, tag: str = ArgPlainText("command")):
    tag = tag.strip()
    msg = await command_server(tag)
    try:
        await mode_txt_to_img("服务器返回", msg)
    except Exception as E:
        await matcher.finish(str(E), reply_message=True)


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
    if anne_ip_dict is None:
        await matcher.finish("网络开小差了捏")
        return
    server_number = len(anne_ip_dict["云"])
    await matcher.finish(f"更新成功\n一共更新了{server_number}个电信anne服ip")


@add2_queries.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    arg_list = arg.extract_plain_text().split(" ")
    if len(arg_list) == 2:
        tag, ip = arg_list
        file_name = f"{tag}.json"
        file_path = DATA_PATH.resolve() / "l4d2" / file_name
        with file_path.open(mode="r", encoding="utf-8") as f:
            tag_data: Dict[str, List[Dict[str, Union[int, str]]]] = json.load(f)
        num_list: List[str] = []
        for one_number in tag_data[tag]:
            num_list.append(str(one_number["id"]))
        add_num = 0
        for i in range(1, 100):
            if str(i) not in num_list:
                add_num = i
                break
            continue
    elif len(arg_list) == 3:
        tag, add_num, ip = arg_list
        file_name = f"{tag}.json"
        file_path = DATA_PATH.resolve() / "l4d2" / file_name
        with file_path.open(mode="r", encoding="utf-8") as f:
            tag_data: Dict[str, List[Dict[str, Union[int, str]]]] = json.load(f)
    else:
        await matcher.finish("参数不正确")
        return
    if add_num != 0:
        tag_data[tag].append({"id": int(add_num), "ip": ip})
        with file_path.open(mode="w", encoding="utf-8") as f:
            json.dump(tag_data, f, ensure_ascii=False)
        await matcher.finish(
            f"""成功添加
            指令: {tag}{add_num}
            ip: {ip}
            """,
        )
    await matcher.finish("参数不正确")


@del2_queries.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    arg_list = arg.extract_plain_text().split(" ")
    if len(arg_list) == 2:
        tag, num = arg_list
        file_name = f"{tag}.json"
        file_path = DATA_PATH.resolve() / "l4d2" / file_name
        with file_path.open(mode="r", encoding="utf-8") as f:
            tag_data: Dict[str, List[Dict[str, Union[int, str]]]] = json.load(f)
        for one_number in tag_data[tag]:
            if str(one_number["id"]) == num:
                tag_data[tag].remove(one_number)
                with file_path.open(mode="w", encoding="utf-8") as f:
                    json.dump(tag_data, f, ensure_ascii=False)
                await matcher.finish(f"成功删除指令指令: {tag}")
    await matcher.finish("参数不正确")


@updata_himi.handle()
async def _(matcher: Matcher):
    send_msg = await get_himi_ip()
    await matcher.finish(send_msg)
