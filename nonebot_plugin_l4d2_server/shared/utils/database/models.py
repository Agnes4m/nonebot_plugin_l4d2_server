from __future__ import annotations

import logging
from typing import ClassVar

from nonebot_plugin_tortoise_orm import add_model
from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model

logger = logging.getLogger(__name__)

try:
    add_model(__name__)
    logger.debug("L4D2 数据库模型注册成功")
except Exception as e:
    logger.exception("L4D2 数据库模型注册失败", exc_info=e)


class SteamUser(Model):
    """Steam 用户资料表"""

    userid = fields.BigIntField(pk=True, description="QQ 用户ID")
    SteamID = fields.TextField(null=True, description="Steam ID")
    SteamID64 = fields.TextField(null=True, description="Steam ID64 格式")
    Name = fields.TextField(null=True, description="Steam 昵称")

    objects: ClassVar[Manager]

    class Meta:  # type: ignore
        table = "steam_user"
        table_description = "L4D2 插件 Steam 用户绑定资料"
