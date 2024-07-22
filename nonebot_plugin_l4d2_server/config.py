from pathlib import Path

from nonebot import get_plugin_config
from pydantic import BaseModel

DATAPATH = Path(__file__).parent.joinpath("data")
DATAOUT = Path("data/L4D2")
server_all_path = DATAOUT / "l4d2"
server_all_path.mkdir(parents=True, exist_ok=True)

ICONPATH = DATAPATH / "icon"


class ConfigModel(BaseModel):
    l4_anne: bool = True
    """是否启用anne电信服相关功能"""
    l4_enable: bool = True
    """是否全局启用求生功能"""
    l4_image: bool = False
    """是否启用图片"""
    l4_connect: bool = True
    """是否在查服命令后加入connect ip"""
    l4_path: str = "data/L4D2"
    """插件数据路径"""
    l4_players: int = 4
    """查询总图的时候展示的用户数量"""
    l4_style: str = "default"
    """图片风格"""
    l4_font: str = str(Path(__file__).parent.joinpath("data/font/loli.ttf"))
    """字体"""


config = get_plugin_config(ConfigModel)
