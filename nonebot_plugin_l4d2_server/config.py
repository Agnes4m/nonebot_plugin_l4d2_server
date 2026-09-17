"""Plugin configuration model.

Pure config schema + ConfigManager; data layout / migration lives in
``services/migrate.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import List  # noqa: F401

from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_MEMBER, GROUP_OWNER
from nonebot.log import logger
from nonebot.permission import SUPERUSER, Permission
from pydantic import BaseModel, Field, field_validator


class ConfigModel(BaseModel):
    """User-tunable configuration."""

    l4_enable: bool = Field(default=True, description="是否全局启用求生功能")
    l4_image: bool = Field(default=True, description="是否启用图片")
    l4_connect: bool = Field(default=True, description="是否在查服命令后加入connect ip")
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
    l4_a2s_concurrency: int = Field(
        default=0, ge=0, le=64,
        description="A2S 并发上限；0=不限（旧版行为：所有服一次性 asyncio.gather），"
        "其他值走 asyncio.Semaphore 节流",
    )
    l4_a2s_timeout: float = Field(default=2.5, gt=0, description="A2S 单次超时秒")
    l4_a2s_cache_ttl: int = Field(default=15, ge=0, description="A2S 结果缓存秒；0=不缓存")
    l4_favorite_check_interval: int = Field(
        default=300, ge=30, description="收藏巡检间隔秒",
    )
    l4_favorite_player_delta: int = Field(
        default=5, ge=1, description="玩家数变化超过此值才推送",
    )
    l4_workshop_concurrency: int = Field(
        default=3, ge=1, le=8, description="创意工坊并发下载数",
    )
    l4_render_timeout: float = Field(
        default=15.0, gt=0,
        description="htmlrender 单次出图硬上限秒；超时/失败/空字节 fallback 到文字",
    )
    l4_history_interval: int = Field(
        default=300, ge=60,
        description="A2S 历史记录周期秒；用于热力图 / Wipe 检测 / 阈值通知",
    )
    l4_history_retention_days: int = Field(
        default=30, ge=1,
        description="A2S 历史保留天数；启动时清理过期记录",
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
        if not isinstance(v, list):
            return v
        validated: list[str] = []
        for path in v:
            if not (Path(path) / "steam_appid.txt").exists():
                # 软警告：缺少 steam_appid.txt 的路径会被跳过，不阻塞插件加载。
                logger.warning(
                    f"l4_local 路径 {path} 下缺少 steam_appid.txt，已忽略",
                )
                continue
            validated.append(str(Path(path).resolve()))
        return validated

    @property
    def l4_permission_set(self) -> Permission:
        permissions = {
            1: SUPERUSER,
            2: SUPERUSER | GROUP_OWNER,
            3: SUPERUSER | GROUP_OWNER | GROUP_ADMIN,
            4: SUPERUSER | GROUP_OWNER | GROUP_ADMIN | GROUP_MEMBER,
        }
        return permissions[self.l4_permission]

    @property
    def data_dir(self) -> Path:
        """数据根目录：``<cwd>/data/nonebot_plugin_l4d2_server/``。"""
        from .services.path_resolver import data_dir as resolve

        return resolve()


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
