
import a2s
from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column

print(a2s.info(("gz.trygek.com", 2334)))
print(a2s.players(("gz.trygek.com", 2334)))


class SteamUser(Model):
    """个人资料"""

    userid: Mapped[str] = mapped_column(primary_key=True)
    SteamID: Mapped[str]
    SteamID64: Mapped[str]
    Name: Mapped[str]
    Name: Mapped[str]
