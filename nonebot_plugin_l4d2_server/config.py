from pathlib import Path

from nonebot import get_plugin_config
from nonebot.log import logger
from pydantic import BaseModel

DATAPATH = Path(__file__).parent.joinpath("data")
DATAOUT = Path("data/L4D2")
if not Path(DATAOUT / "l4d2.json").exists():
    logger.info("文件 l4d2.json 不存在，已创建并初始化为 {}")
    Path(DATAOUT / "l4d2.json").write_text("{}", encoding="utf-8")
print(DATAOUT.absolute())
server_all_path = DATAOUT / "l4d2"
server_all_path.mkdir(parents=True, exist_ok=True)

ICONPATH = DATAPATH / "icon"

global map_index
map_index = 0


class ConfigModel(BaseModel):
    l4_enable: bool = True
    """是否全局启用求生功能"""
    l4_image: bool = True
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
    l4_show_ip: bool = True
    """单服务器查询时候是否展示ip直连地址"""
    l4_local: list[str] = []
    """本地服务器路径,填写路径下有`steam_appid.txt`文件"""


config = get_plugin_config(ConfigModel)


class ConfigManager:
    """配置项管理类，提供类型安全的配置更新方法"""

    def __init__(self):
        self._config = config

    def update_image_config(self, enabled: bool) -> None:
        """更新图片配置

        Args:
            enabled: 是否启用图片功能
        """
        self._config.l4_image = enabled

    def update_style_config(self, style: str) -> None:
        """更新图片风格配置

        Args:
            style: 图片风格名称
        """
        if not isinstance(style, str):
            raise TypeError("style必须是字符串")
        self._config.l4_style = style

    def update_connect_config(self, enabled: bool) -> None:
        """更新connect ip配置

        Args:
            enabled: 是否在查服命令后加入connect ip
        """
        self._config.l4_connect = enabled

    def update(self, **kwargs) -> None:
        """通用配置更新方法

        Args:
            **kwargs: 要更新的配置项键值对

        Raises:
            ValueError: 当传入无效的配置项时
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                raise ValueError(f"无效的配置项: {key}")


config_manager = ConfigManager()
