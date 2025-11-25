from nonebot.matcher import Matcher
from nonebot.rule import command as command_rule

from ..l4_request import COMMAND


def refresh_server_command_rule(l4_request: type[Matcher]) -> None:
    """根据最新的服务器组刷新命令别名"""
    commands = {"anne"}
    commands.update(COMMAND)
    l4_request.rule = command_rule(*commands)
