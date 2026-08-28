"""User-facing message strings (text responses sent back to chat)."""

from __future__ import annotations

from typing import ClassVar


class Gm:
    """Generic messages (commands / queries)."""

    no_id = "请输入正确的 ID"
    outputing_group = "正在输出组"
    add_name = "请在指令后添加要找的昵称哦"
    no_found = "未找到这个组"
    no_player = "未找到玩家"


class Sm:
    """Server-related messages."""

    server_not_found = "未找到该服务器"
    server_mistake = "服务器错误"
    server_outtime = "服务器无响应"
    no_group_search = "未设置组，正在全服查找，时间较长"
    no_player = "未找到玩家"
    searching = "正在搜索"
    other_wrong = "其他错误"
    no_get = "未获取到服务器数据"

    no_player_info: ClassVar[list[str]] = [
        "服务器感觉很安静啊",
        "服务器里是空空的呢",
        "这里没有格林达姆",
        "也许服务器还有一个幽灵",
    ]
