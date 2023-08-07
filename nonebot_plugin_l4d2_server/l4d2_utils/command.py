import re

from nonebot import on_command, on_notice, on_regex

from .config import MASTER
from .rule import wenjian

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
