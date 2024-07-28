# coding=utf-8
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


class AnnePlayerDetail(TypedDict):
    rank: int
    source: str
    avg_source: float
    kills: str
    kills_people: str
    headshots: str
    avg_headshots: float
    map_play: str


class AnnePlayerError(TypedDict):
    mistake_shout: str
    kill_friend: str
    down_friend: str
    abandon_friend: str
    put_into: str
    agitate_witch: str


class AnnePlayerInfAvg(TypedDict):
    avg_smoker: float
    avg_boomer: float
    avg_hunter: float
    avg_charger: float
    avg_spitter: float
    avg_jockey: float
    avg_tank: float


class AnnePlayerSur(TypedDict):
    map_clear: str
    prefect_into: str
    get_oil: str
    ammo_arrange: str
    adrenaline_give: str
    pills_give: str
    """给药"""
    first_aid_give: str
    """给包"""
    friend_up: str
    diss_friend: str
    save_friend: str
    protect_friend: str
    pro_from_smoker: str
    pro_from_hunter: str
    pro_from_charger: str
    pro_from_jockey: str
    melee_charge: str
    """刀牛"""
    tank_kill: str
    witch_instantly_kill: str
    """秒妹"""


class AnnePlayerInf(TypedDict):
    sur_ace: str
    sur_down: str
    boommer_hit: str
    hunter_prefect: str
    hunter_success: str
    tank_damage: str
    charger_multiple: str


class AnnePlayerInfo(TypedDict):
    name: str
    avatar: str
    steamid: str
    playtime: str
    lasttime: str


class AnnePlayer2(TypedDict):
    kill_msg: str
    info: AnnePlayerInfo
    detail: AnnePlayerDetail
    error: AnnePlayerError
    inf_avg: AnnePlayerInfAvg
    sur: AnnePlayerSur
    inf: AnnePlayerInf
