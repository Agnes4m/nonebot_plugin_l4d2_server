from typing import Union

from nonebot.rule import Rule
from nonebot.params import Depends, CommandArg
from nonebot.adapters.onebot.v11 import Message, NoticeEvent
from nonebot.adapters.onebot.v11.event import MessageEvent as V11MessageEvent
from nonebot.adapters.onebot.v12.event import MessageEvent as V12MessageEvent
from nonebot.adapters.kaiheila.event import MessageEvent as kaiheilaMessageEvent
from nonebot.adapters.qqguild.event import MessageEvent as qqguidMessageEvent

from nonebot.adapters.onebot.v11 import Message  as V11Message
from nonebot.adapters.onebot.v12 import Message  as V12Message
from nonebot.adapters.kaiheila import Message as kaiheilaMessage
from nonebot.adapters.qqguild import Message as qqguidMessage

from nonebot.adapters.onebot.v11.event import NoticeEvent as V11NoticeEvent
from nonebot.adapters.onebot.v12.event import NoticeEvent as V12NoticeEvent
from nonebot.adapters.kaiheila.event import NoticeEvent as kaiheilaNoticeEvent

from nonebot.adapters.onebot.v11 import MessageSegment as V11MessageSegment
from nonebot.adapters.onebot.v12 import MessageSegment as V12MessageSegment
from  nonebot.adapters.kaiheila import MessageSegment as kaiheilaMessageSegment
from  nonebot.adapters.qqguild import MessageSegment as qqguidMessageSegment

from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GroupMessageEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as V12GroupMessageEvent
from  nonebot.adapters.kaiheila.event import ChannelMessageEvent as kaiheilaChannelMessageEvent
from  nonebot.adapters.qqguild import ChannelEvent as qqguidChannelEvent

Event_ = Union[
    V11MessageEvent, V12MessageEvent,kaiheilaMessageEvent, qqguidMessageEvent
]
Message_ = Union[
    V11Message, V12Message,kaiheilaMessage, qqguidMessage
]
NoticeEvent_ = Union[
    V11NoticeEvent, V12NoticeEvent,kaiheilaNoticeEvent
]
GroupEvent_ = Union[V11GroupMessageEvent,V12GroupMessageEvent,kaiheilaChannelMessageEvent,qqguidChannelEvent]
from nonebot_plugin_saa import Image, Text, MessageFactory
from nonebot_plugin_saa import extract_target, get_target, PlatformTarget
from nonebot_plugin_saa import (
    TargetQQGroup,
    TargetQQGuildChannel,
    TargetOB12Unknow,
    TargetKaiheilaChannel,
)
MessageSegment_ = Union[V11MessageSegment,V12MessageSegment,kaiheilaMessageSegment,qqguidMessageSegment]


from .config import l4_config, file_format


async def full_command(arg: Message = CommandArg()) -> bool:
    return not bool(str(arg))


def FullCommand() -> Rule:
    return Rule(full_command)


def FullCommandDepend():
    return Depends(full_command)


def wenjian(event: NoticeEvent):
    args = event.dict()
    try:
        name: str = args["file"]["name"]
        usr_id = str(args["user_id"])
    except KeyError:
        return False
    if args["notice_type"] == "offline_file":
        if l4_config.l4_master:
            return name.endswith(file_format) and usr_id in l4_config.l4_master
        else:
            return name.endswith(file_format)
    elif args["notice_type"] == "group_upload":
        if l4_config.l4_master:
            return usr_id in l4_config.l4_master and name.endswith(file_format)
        else:
            return False
    return False
