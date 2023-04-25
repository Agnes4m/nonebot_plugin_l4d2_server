"""from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path

from pydantic import BaseModel, Field

from ruamel import yaml


CONFIG_PATH = Path() / 'data' / 'L4D2' / 'l4d2.yml'
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

class L4d2GroupConfig(BaseModel):
    enable: bool = Field(True, alias='是否启用求生功能')
    map_master: List[str] = Field([], alias='分群地图管理员')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)


class L4d2Config(BaseModel):
    total_enable: bool = Field(True, alias='是否全局启用求生功能')
    map_path: List[str] = Field([], alias='求生地图路径')
    web_username: str = Field('l4d2', alias='后台管理用户名')
    web_password: str = Field('admin', alias='后台管理密码')
    l4_file: List[str] = Field(	["/home/ubuntu/l4d2/coop"], alias='本地求生服务器地址')
    l4_host: List[str] = Field(['127.0.0.1'], alias='求生服务器地址')
    l4_port: List[str] = Field(['20715'], alias='求生服务器端口')
    l4_rcon: List[str] = Field(['114514'], alias='求生服务器rcon密码')
    l4_ipall: Dict[str,Dict[str,str]] = Field(
        {'本地地图':{
        'place':'local',
        'location':'C:\\l4d2',
        'host':'127.0.0.1',
        'port':'20715',
        'rcon':'114514'
        },
        '远程地图':{
        'place':'remote',
        'location':'/home/unbuntu/coop',
        'host':'11.4.51.4',
        'port':'20715',
        'rcon':'9191810'
        },
          },
          alias='求生服务器ip集合')
    web_secret_key: str = Field('49c294d32f69b732ef6447c18379451ce1738922a75cd1d4812ef150318a2ed0',
                                alias='后台管理token密钥')
    l4_master: List[str] = Field([], alias='求生地图全局管理员qq')
    l4_ip:bool = Field(False, alias='查询地图是否显示ip')
    l4_font: str = Field('simsun.ttc', alias='字体')
    l4_only:bool = Field(False, alias='下载地图是是否阻碍其他指令')
    l4_tag: List[str] = Field(['呆呆','橘'], alias='查服的名')
    l4_key: str = Field('1145149191810', alias='l4_key')
    group_config: Dict[int, L4d2GroupConfig] = Field({}, alias='分群配置')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)
                            
class L4d2ConfigManager:

    def __init__(self):
        self.file_path = CONFIG_PATH
        if self.file_path.exists():
            self.config = L4d2Config.parse_obj(
                yaml.load(self.file_path.read_text(encoding='utf-8'), Loader=yaml.Loader))
        else:
            self.config = L4d2Config()
        self.save()

    def get_group_config(self, group_id: int) -> L4d2GroupConfig:
        if group_id not in self.config.group_config:
            self.config.group_config[group_id] = L4d2GroupConfig()
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
            
config_manager = L4d2ConfigManager()

class UserModel(BaseModel):
    username: str
    password: str
    """