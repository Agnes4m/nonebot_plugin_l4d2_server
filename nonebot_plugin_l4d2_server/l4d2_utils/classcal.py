from typing import List

from pydantic import BaseModel


class PlayerInfo(BaseModel):
    """读取玩家信息"""

    name: str = ""
    Score: int = 0
    Duration: str = ""


class ServerStatus(BaseModel):
    """单服务器查询信息"""

    name: str = "null"
    """服务器名称"""
    map_: str = "null"
    """服务器地图"""
    players: int = 0
    """当前玩家数量"""
    Players: List[PlayerInfo] = []
    """当前玩家信息"""
    max_players: int = 0
    """最大玩家数量"""
    rank_players: str = "null"
    """玩家数量对比"""
    ping: str = "null"
    """服务器延迟"""
    number: str = "null"
    """服务器序号"""
    ip: str = "null"
    """服务器ip"""
    system: str = "m.svg"
    """服务器系统，["l","w","m"]"""


class ServerGroup(BaseModel):
    """组服务器信息"""

    server_id: int = 0
    """服务器序号"""
    server_number: int = 0
    """群组当期启动服务器数量"""
    server_all_number: int = 0
    """群组总服务器数量"""
    server_people: int = 0
    """群组当前在线人数"""
    server_all_people: int = 0
    """群组当前总容纳人数"""
