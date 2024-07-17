from typing import Optional, TypedDict

from pydantic import BaseModel


class SourceBansInfo(BaseModel):
    """source服务器信息"""

    index: int
    host: str
    port: int


class NserverDetail(TypedDict):
    id: int
    ip: Optional[str]
    host: Optional[str]
    port: Optional[int]
    version: Optional[str]


class NserverOut(TypedDict):
    id: int
    ip: str
    host: str
    port: int
    version: Optional[str]
