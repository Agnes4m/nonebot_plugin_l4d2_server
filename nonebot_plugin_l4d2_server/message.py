from typing import ClassVar


class Gm:
    no_id: str = "请输入正确的 ID"
    outputing_group: str = "正在输出组"
    add_name: str = "请在指令后添加要找的昵称哦"
    no_found: str = "未找到这个组"


class Sm:
    server_not_found: str = "未找到该服务器"
    server_mistake: str = "服务器错误"
    server_outtime: str = "服务器无响应"
    no_group_search: str = "未设置组，正在全服查找，时间较长"
    no_player: str = "未找到玩家"
    searching: str = "正在搜索"
    other_wrong: str = "其他错误"
    no_get: str = "未获取到服务器数据"
    no_player_info: ClassVar[list[str]] = [
        "服务器感觉很安静啊",
        "服务器里是空空的呢",
        "这里没有格林达姆",
        "也许服务器还有一个幽灵",
    ]
