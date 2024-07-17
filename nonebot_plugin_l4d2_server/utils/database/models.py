from pathlib import Path
from typing import List, Optional

import nonebot_plugin_localstore as store
import yaml
from nonebot import get_driver, on_command, require
from nonebot.params import Depends
from nonebot_plugin_datastore import get_plugin_data, get_session
from pydantic import BaseModel, Field
from pydantic.json import pydantic_encoder
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlmodel import Field

plugin_data = get_plugin_data()

# 定义模型
DATA = get_plugin_data()
DATA.set_migration_dir(Path("data/L4D2/") / "sql")


class SteamUser(DATA.Model):
    """个人资料"""

    SteamID: Mapped[str] = mapped_column(primary_key=True)
    SteamID64: Mapped[str]
    Name: Mapped[str]


matcher = on_command("test")

# 数据库相关操作
# @matcher.handle()
# async def handle(session: AsyncSession = Depends(get_session)):
#     example = SteamUser(message="matcher")
#     session.add(example)
#     await session.commit()