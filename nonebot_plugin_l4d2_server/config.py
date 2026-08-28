"""Plugin configuration model.

Pure config schema + ConfigManager; data layout / migration lives in
``services/migrate.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_MEMBER, GROUP_OWNER
from nonebot.log import logger
from nonebot.permission import SUPERUSER, Permission
from pydantic import BaseModel, Field, field_validator

from consts import DEFAULT_DATA_DIR


class ConfigModel(BaseModel):
    """User-tunable configuration."""

    l4_enable: bool = Field(default=True, description="是否全局启用求生功能")
    l4_image: bool = Field(default=True, description="是否启用图片")
    l4_connect: bool = Field(default=True, description="是否在查服命令后加入connect ip")
    l4_path: str = Field(default=DEFAULT_DATA_DIR, description="插件数据路径")
    l4_players: int = Field(default=4, ge=1, description="查询总图时展示的用户数量")
    l4_style: str = Field(default="default", description="图片风格")
    l4_font: str = Field(default="", description="字体文件路径")
    l4_show_ip: bool = Field(
        default=True,
        description="单服务器查询时是否展示ip直连地址",
    )
    l4_local: List[str] = Field(default=[], description="本地服务器路径列表")
    l4_map_index: int = Field(default=0, description="地图索引")
    l4_permission: int = Field(
        default=1,
        ge=1,
        le=4,
        description="上传地图权限",
    )

    @field_validator("l4_players")
    @classmethod
    def validate_players(cls, v):
        if v < 1:
            v = 1
            logger.warning("玩家数量必须大于0, 默认设置为1")
        return v

    @field_validator("l4_local", mode="before")
    @classmethod
    def validate_local_paths(cls, v):
        if isinstance(v, list):
            validated: list[str] = []
            for path in v:
                if not (Path(path) / "steam_appid.txt").exists():
                    raise ValueError(f"路径 {path} 下缺少 steam_appid.txt 文件")
                validated.append(str(Path(path).resolve()))
            return validated
        return v

    @property
    def l4_permission_set(self) -> Permission:
        permissions = {
            1: SUPERUSER,
            2: SUPERUSER | GROUP_OWNER,
            3: SUPERUSER | GROUP_OWNER | GROUP_ADMIN,
            4: SUPERUSER | GROUP_OWNER | GROUP_ADMIN | GROUP_MEMBER,
        }
        return permissions[self.l4_permission]


config = get_plugin_config(ConfigModel)


class ConfigManager:
    """Runtime config toggle helpers."""

    def __init__(self) -> None:
        self._config = config

    def update_image_config(self, enabled: bool) -> None:
        self._config.l4_image = enabled

    def update_style_config(self, style: str) -> None:
        if not isinstance(style, str):
            raise TypeError("style必须是字符串")
        self._config.l4_style = style


config_manager = ConfigManager()