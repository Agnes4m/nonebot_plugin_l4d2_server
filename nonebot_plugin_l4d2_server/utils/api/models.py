from typing import List, Optional, TypedDict

import a2s
from pydantic import BaseModel


class SourceBansInfo(BaseModel):
    """source服务器信息"""

    index: int
    host: str
    port: int


class NserverOut(TypedDict):
    id: int
    ip: str
    host: str
    port: int
    version: Optional[str]


class OutServer(TypedDict):
    server: a2s.SourceInfo
    player: List[a2s.Player]
    host: str
    port: int
    command: str
    id_: int


class AnnePlayer(TypedDict):
    mode: str
    name: str
    source: str
    playtime: str


class AllServer(TypedDict):
    command: str
    active_server: int
    max_server: int
    active_player: int
    max_player: int


class AnneSearch(TypedDict):
    steamid: str
    rank: str
    name: str
    score: str
    play_time: str
    last_time: str
