"""User-facing message strings (text responses sent back to chat)."""

from __future__ import annotations

from typing import ClassVar, Iterable

# QQ 等平台单条文字消息过长会直接发送失败；长列表按行切成多条，留足余量。
MAX_TEXT_CHARS = 2000


def split_message(lines: Iterable[str], max_chars: int = MAX_TEXT_CHARS) -> list[str]:
    """把多行文本按行打包成若干条消息，每条不超过 ``max_chars`` 字符。

    单行本身就超长时按长度硬切，保证每条都发得出去。没有内容返回空列表。
    """
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for line in lines:
        pieces = [line[i : i + max_chars] for i in range(0, len(line), max_chars)]
        for piece in pieces or [""]:
            if buf and size + 1 + len(piece) > max_chars:
                chunks.append("\n".join(buf))
                buf, size = [], 0
            size += len(piece) + (1 if buf else 0)
            buf.append(piece)
    if buf:
        chunks.append("\n".join(buf))
    return chunks


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
    server_blocked = "该服务器已被屏蔽"
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


class Wm:
    """Workshop (创意工坊) messages."""

    workshop_summary = (
        "工坊批量下载完成：共 {total} 个，成功 {ok}，重复 {duplicate}，失败 {failed}"
    )
