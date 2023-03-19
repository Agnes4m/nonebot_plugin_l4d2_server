from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path

from pydantic import BaseModel, Field

from nonebot import get_driver, logger
from ruamel import yaml


CONFIG_PATH = Path() / 'data' / 'L4D2' / 'l4d2.yml'
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

class ChatGroupConfig(BaseModel):
    enable: bool = Field(True, alias='是否启用求生功能')
    map_master: List[str] = Field([], alias='分群地图管理员')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)


class ChatConfig(BaseModel):
    total_enable: bool = Field(True, alias='是否全局启用求生功能')
    map_path: List[str] = Field([], alias='求生地图路径')
    web_username: str = Field('chat', alias='后台管理用户名')
    web_password: str = Field('admin', alias='后台管理密码')
    server_host: List[str] = Field([], alias='求生服务器地址')
    server_port: List[str] = Field([], alias='求生服务器端口')
    server_password: List[str] = Field([], alias='求生服务器rcon密码')
    web_secret_key: str = Field('49c294d32f69b732ef6447c18379451ce1738922a75cd1d4812ef150318a2ed0',
                                alias='后台管理token密钥')
    map_master: List[str] = Field([], alias='求生地图全局管理员qq')
    only_download:bool = Field(False, alias='下载地图是是否阻碍其他指令')
    api_token: str = Field('', alias='api的token')
    group_config: Dict[int, ChatGroupConfig] = Field({}, alias='分群配置')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)
                
class ChatConfigManager:

    def __init__(self):
        self.file_path = CONFIG_PATH
        if self.file_path.exists():
            self.config = ChatConfig.parse_obj(
                yaml.load(self.file_path.read_text(encoding='utf-8'), Loader=yaml.Loader))
        else:
            self.config = ChatConfig()
        self.save()

    def get_group_config(self, group_id: int) -> ChatGroupConfig:
        if group_id not in self.config.group_config:
            self.config.group_config[group_id] = ChatGroupConfig()
            self.save()
        return self.config.group_config[group_id]

    @property
    def config_list(self) -> List[str]:
        return list(self.config.dict(by_alias=True).keys())

    def save(self):
        with self.file_path.open('w', encoding='utf-8') as f:
            yaml.dump(
                self.config.dict(by_alias=True),
                f,
                indent=2,
                Dumper=yaml.RoundTripDumper,
                allow_unicode=True)
            
config_manager = ChatConfigManager()

class UserModel(BaseModel):
    username: str
    password: str