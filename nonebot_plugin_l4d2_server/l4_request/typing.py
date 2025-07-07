from dataclasses import dataclass
from typing import Dict, List, Tuple, TypedDict

from ..utils.api.models import NserverOut

ServerList = List[NserverOut]
ServerDict = Dict[str, ServerList]
ServerInfo = Tuple[str, int]
PlayerList = List[Dict]  # 假设玩家对象的类型，应根据实际情况定义更具体的类型

DEFAULT_MAP_TYPES = ["普通药役", "硬核药役"]
FILTER_MODES = {"tj", "zl", "kl"}

ALLHOST: ServerDict = {}  # 保留原始全局变量名以兼容现有代码
COMMAND: set[str] = set()


@dataclass
class ServerStats:
    active_servers: int
    total_servers: int
    active_players: int
    max_players: int


class ServerResponse(TypedDict):
    command: str
    active_server: int
    max_server: int
    active_player: int
    max_player: int


# 全局变量使用更明确的命名
SERVER_REGISTRY: ServerDict = {}
REGISTERED_COMMANDS: set[str] = set()
