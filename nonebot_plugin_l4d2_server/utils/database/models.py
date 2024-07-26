from pathlib import Path

# 导入插件方法
from nonebot_plugin_tortoise_orm import add_model
from tortoise import fields
from tortoise.models import Model

# Path("data/L4D2/") / "sql")

add_model(__name__)

class SteamUser(Model):
    """个人资料"""
    userid = fields.BigIntField(pk=True)
    SteamID = fields.TextField()
    SteamID64= fields.TextField()
    Name= fields.TextField()
    
    class Meta:
        table = "steam_user"
        table_description = "个人资料"