from pathlib import Path
import re
import a2s
from typing import Dict, Union, Optional, Any

try:
    import ujson as json
except:
    import json

from nonebot.log import logger
from nonebot import get_driver, on_command, get_bot
from nonebot import require
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import  MessageSegment
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from ..l4d2_utils.rule import MessageFactory,Image,Text,GroupEvent_,Message_
from ..l4d2_utils.command import get_ip_to_mes
from ..l4d2_utils.utils import extract_last_digit, split_maohao,get_group_id
from ..l4d2_queries.utils import json_server_to_tag_dict, queries_dict
from ..l4d2_utils.config import l4_config

driver = get_driver()
sch_json = Path("data/L4D2/scheduler.json")
if not sch_json.exists():
    with sch_json.open("w") as f:
        json.dump({}, f, ensure_ascii=False)

add_rss = on_command(
    "add_rss",
    aliases={"求生定时添加"},
    priority=30,
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
)
del_rss = on_command(
    "del_rss",
    aliases={"求生定时删除"},
    priority=30,
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
)


@add_rss.handle()
async def _(event: GroupEvent_, matcher: Matcher, args: Message_ = CommandArg()):
    group_id = get_group_id(event)
    if not group_id:
        return
    msg = args.extract_plain_text()
    command, message = await extract_last_digit(msg)
    push_msg = await get_ip_to_mes(msg=message, command=command)
    if not push_msg:
        return
    if push_msg in ["服务器无响应", None]:
        await matcher.finish("无响应的服务器，请检查")
    else:
        return_msg = await add_or_update_data(group_id, msg)
        if isinstance(push_msg, bytes):
            await MessageFactory([Image(push_msg)]).send()
        elif isinstance(push_msg, MessageFactory):
            await push_msg.send()
        else:
            await matcher.send(push_msg)
        if return_msg == "add":
            await matcher.send(f"已添加群定时任务【{msg}】{l4_config.l4_push_times}次")
        elif return_msg in ["update", "change"]:
            await matcher.send(f"已更新群定时任务【{msg}】{l4_config.l4_push_times}次")


@del_rss.handle()
async def _(event: GroupEvent_, matcher: Matcher):
    group_id = get_group_id(event)
    if not group_id:
        return
    await add_or_update_data(group_id, "", ad_mode="del")
    await matcher.finish("已删除群定时任务")


async def add_or_update_data(group_i: int, some_str: str = "", ad_mode: str = "add"):
    """添加或者删除定时任务
    mode == [new,update,del,change]
    """
    group_id = str(group_i)
    sch_json = Path("data/L4D2/scheduler.json")
    if ad_mode == "add":
        if sch_json.exists():
            with sch_json.open(encoding="utf-8") as f:
                scheduler_data = json.load(f)
            try:
                msg_dict = scheduler_data[group_id]
                times = msg_dict["times"]
                old_msg = msg_dict["msg"]
                scheduler_data[group_id] = {
                    "times": l4_config.l4_push_times,
                    "msg": some_str,
                }
                if old_msg == some_str:
                    mode = "update"
                else:
                    mode = "change"
            except:
                scheduler_data[group_id] = {
                    "times": l4_config.l4_push_times,
                    "msg": some_str,
                }
                mode = "new"

        else:
            scheduler_data = {
                group_id: {"times": l4_config.l4_push_times, "msg": some_str}
            }
            mode = "new"

        with sch_json.open("w", encoding="utf-8") as f:
            json.dump(scheduler_data, f, ensure_ascii=False)

    else:
        if sch_json.exists():
            with sch_json.open() as f:
                scheduler_data: Dict[str, Dict[str, Union[str, int]]] = json.load(f)
            try:
                msg_dict = scheduler_data[group_id]
                times = msg_dict["times"]
                old_msg = msg_dict["msg"]
                scheduler_data[group_id] = {"times": 0, "msg": old_msg}
            except:
                scheduler_data[group_id] = {"times": 0, "msg": some_str}
        else:
            scheduler_data = {group_id: {"times": 0, "msg": some_str}}
        mode = "del"

        with sch_json.open("w", encoding="utf-8") as f:
            json.dump(scheduler_data, f, ensure_ascii=False)

    return mode


async def rss_ip():
    """推送一次"""
    sch_json = Path("data/L4D2/scheduler.json")

    if sch_json.exists():
        with sch_json.open(encoding="utf-8") as f:
            scheduler_data: Dict[str, Dict[str, Union[int, str]]] = json.load(f)

            for key, value in scheduler_data.items():
                try:
                    recipient_id = int(key)
                    count = value["times"]
                    msg = str(value["msg"])
                    count = int(count)

                    if count > 0:
                        msg_read = await send_message(recipient_id, msg, value)
                        if msg_read and isinstance(msg_read, str):
                            scheduler_data[key]["ip_detail"] = msg_read
                        count -= 1

                    scheduler_data[key]["times"] = count
                except TypeError:
                    continue

        with sch_json.open(mode="w", encoding="utf-8") as f:
            json.dump(scheduler_data, f, ensure_ascii=False)


async def send_message(
    recipient_id: int, msg: str, value: Optional[Dict[str, Union[int, str]]] = None
):
    # 执行发送消息的操作，参数可以根据需要进行传递和使用
    command, message = await extract_last_digit(msg)
    push_msg = await get_ip_to_mes(msg=message, command=command)
    if isinstance(push_msg, bytes):
        await get_bot().send_group_msg(
            group_id=recipient_id, message=MessageSegment.image(push_msg)
        )
    elif msg and isinstance(push_msg, str):
        # 单服务器
        message = await json_server_to_tag_dict(msg, command)
        if len(message) == 0 or not value:
            # 关键词不匹配，忽略
            return
        try:
            old_msg = value.get("ip_detail", {})
            if not isinstance(old_msg, dict):
                return
            ip = str(message["ip"])
            host, port = split_maohao(ip)
            msg_: a2s.SourceInfo = await a2s.ainfo((host, port))
            value["map_"] = msg_.map_name
            value["rank_players"] = f"{msg_.player_count}/{msg_.max_players}"
            if (
                old_msg["map_"] == value["map_"]
                and old_msg["rank_players"] == value["rank_players"]
            ):
                logger.info(f"{msg}{command}人数和地图未发生变化")
            else:
                await get_bot().send_group_msg(group_id=recipient_id, message=push_msg)
        except Exception as e:
            logger.warning(e)

        return value


async def server_is_change():
    """检测服务器是否发生变化"""


# @driver.on_bot_connect
# async def _():
#     logger.success("已成功启动求生定时推送")
#     scheduler.add_job(
#         rss_ip, "interval", minutes=l4_config.l4_push_interval, id="rss_ip"
#     )
