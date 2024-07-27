from nonebot_plugin_tortoise_orm import add_model
from tortoise import fields
from tortoise.models import Model

add_model(__name__)


class SteamUser(Model):
    """个人资料"""

    userid = fields.BigIntField(pk=True)
    SteamID = fields.TextField(null=True)
    SteamID64 = fields.TextField(null=True)
    Name = fields.TextField(null=True)

    class Meta:  # type: ignore
        table = "steam_user"
        table_description = "个人资料"
