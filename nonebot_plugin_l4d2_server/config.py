from pathlib import Path
from typing import List, Set

from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_MEMBER, GROUP_OWNER
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from pydantic import BaseModel, Field, field_validator

# 常量定义
DATAPATH = Path(__file__).parent.joinpath("data")
DEFAULT_DATA_DIR = "data/L4D2"
DEFAULT_FONT = str(Path(__file__).parent.joinpath("data/font/loli.ttf"))


# 初始化数据目录
def init_data_directory(data_dir: Path) -> None:
    """初始化数据目录和必要文件"""
    data_dir.mkdir(parents=True, exist_ok=True)
    json_file = data_dir / "l4d2.json"

    if not json_file.is_file():
        logger.info(f"文件 {json_file.name} 不存在，已创建并初始化为 {{}}")
        json_file.write_text("{}", encoding="utf-8")


# 初始化目录结构
DATAOUT = Path(DEFAULT_DATA_DIR)
init_data_directory(DATAOUT)
init_data_directory(DATAOUT / "l4d2")
server_all_path = DATAOUT / "l4d2"
server_all_path.mkdir(parents=True, exist_ok=True)

ICONPATH = DATAPATH / "icon"


class ConfigModel(BaseModel):
    """插件配置模型"""

    l4_enable: bool = Field(default=True, description="是否全局启用求生功能")
    l4_image: bool = Field(default=True, description="是否启用图片")
    l4_connect: bool = Field(default=True, description="是否在查服命令后加入connect ip")
    l4_path: str = Field(default=DEFAULT_DATA_DIR, description="插件数据路径")
    l4_players: int = Field(default=4, ge=1, description="查询总图时展示的用户数量")
    l4_style: str = Field(default="default", description="图片风格")
    l4_font: str = Field(default=DEFAULT_FONT, description="字体文件路径")
    l4_show_ip: bool = Field(
        default=True,
        description="单服务器查询时是否展示ip直连地址",
    )
    l4_local: List[str] = Field(default=[], description="本地服务器路径列表")
    l4_map_index: int = Field(default=0, description="地图索引")
    l4_permission: int = Field(
        default=1,  # 默认为1，只包括SUPERUSER
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
            validated_paths = []
            for path in v:
                path_obj = Path(path)
                if not (path_obj / "steam_appid.txt").exists():
                    raise ValueError(f"路径 {path} 下缺少 steam_appid.txt 文件")
                validated_paths.append(str(path_obj.resolve()))
            return validated_paths
        return v

    def update_map_index(self, index: int) -> None:
        """更新地图索引配置"""
        if index < 0:
            raise ValueError("地图索引不能小于0")
        self._config.map_index = index

    @property
    def l4_permission_set(self) -> Set[int]:
        permissions = {
            1: SUPERUSER,
            2: SUPERUSER | GROUP_OWNER,
            3: SUPERUSER | GROUP_OWNER | GROUP_ADMIN,
            4: SUPERUSER | GROUP_OWNER | GROUP_ADMIN | GROUP_MEMBER,
        }
        return permissions[self.l4_permission]


config = get_plugin_config(ConfigModel)


class ConfigManager:
    """配置项管理类，提供类型安全的配置更新方法"""

    def __init__(self):
        self._config = config

    @property
    def current_config(self) -> ConfigModel:
        """获取当前配置"""
        return self._config

    def update_image_config(self, enabled: bool) -> None:
        """更新图片配置"""
        self._config.l4_image = enabled

    def update_style_config(self, style: str) -> None:
        """更新图片风格配置"""
        if not isinstance(style, str):
            raise TypeError("style必须是字符串")
        self._config.l4_style = style

    def update_connect_config(self, enabled: bool) -> None:
        """更新connect ip配置"""
        self._config.l4_connect = enabled

    def update(self, **kwargs) -> None:
        """
        通用配置更新方法

        Args:
            **kwargs: 要更新的配置项键值对

        Raises:
            ValueError: 当传入无效的配置项或值不合法时
            TypeError: 当传入值的类型不正确时
        """
        valid_keys = ConfigModel.model_fields.keys()

        for key, value in kwargs.items():
            if key not in valid_keys:
                raise ValueError(f"无效的配置项: {key}")

            field_type = ConfigModel[key].type_
            if not isinstance(value, field_type):
                raise TypeError(f"{key} 必须是 {field_type.__name__} 类型")

            setattr(self._config, key, value)

        # 验证更新后的配置
        try:
            self._config = ConfigModel(**self._config.dict())
        except ValueError as e:
            logger.error(f"配置更新失败: {e!s}")


config_manager = ConfigManager()
