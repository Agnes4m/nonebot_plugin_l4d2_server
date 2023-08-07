from nonebot import on_command

from .config import MASTER

help_ = on_command("l4_help", aliases={"求生帮助"}, priority=20, block=True)


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
