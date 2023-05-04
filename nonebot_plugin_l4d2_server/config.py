from pathlib import Path
from typing import List,Dict,Union
import ast
import platform
import os
from ruamel import yaml
from pydantic import Extra,BaseModel,Field
try:
    import ujson as json
except:
    import json

from nonebot.permission import SUPERUSER
from nonebot import get_driver
from nonebot.log import logger
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
    PRIVATE_FRIEND,
)

from .l4d2_queries.ohter import ALL_HOST
file_format = (".vpk",".zip",".7z",'rar')
# 权限

driver = get_driver()
COMMAND_START = list[driver.config.command_start]
try:
    NICKNAME: str = list(driver.config.nickname)[0]
except Exception:
    NICKNAME = 'bot'
CHECK_FILE:int = 0


reMaster = SUPERUSER | GROUP_OWNER 
Master = SUPERUSER | GROUP_ADMIN | GROUP_OWNER 
ADMINISTRATOR = SUPERUSER | GROUP_ADMIN | GROUP_OWNER | PRIVATE_FRIEND
# file 填写求生服务器所在路径




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
    l4_style: str = Field("standard", alias='图片风格')
    # l4_file: List[str] = Field(	["/home/ubuntu/l4d2/coop"], alias='本地求生服务器地址')
    # l4_host: List[str] = Field(['127.0.0.1'], alias='求生服务器地址')
    # l4_port: List[str] = Field(['20715'], alias='求生服务器端口')
    # l4_rcon: List[str] = Field(['114514'], alias='求生服务器rcon密码')
    
    l4_ipall: List[Dict[str,Union[str,int,bool]]] = Field(
        [{
        'id_rank':'1',
        'place': False,
        'location':'C:\\l4d2',
        'host':'127.0.0.1',
        'port':'20715',
        'rcon':'114514',
        'server_id':'本地地图',
        },{
        'id_rank':'2',
        'place': True,
        'location':'/home/unbuntu/coop',
        'host':'11.4.51.4',
        'port':'20715',
        'rcon':'9191810',
        'account':'root',
        'password':'114514',
        'server_id':'远程地图',
        }],
          alias='l4服务器ip集合')
    web_secret_key: str = Field('49c294d32f69b732ef6447c18379451ce1738922a75cd1d4812ef150318a2ed0',
                                alias='后台管理token密钥')
    l4_master: List[str] = Field(['114514919'], alias='求生地图全局管理员qq')
    # l4_ip:bool = Field(False, alias='查询地图是否显示ip')
    l4_font: str = Field('simsun.ttc', alias='字体')
    l4_only:bool = Field(False, alias='下载地图是是否阻碍其他指令')
    l4_tag: List[str] = Field(['呆呆','橘'], alias='查服的名')
    l4_key: str = Field('q1145149191810', alias='key')
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

# 参数设置为全局变量
global config_manager,l4_config            
config_manager = L4d2ConfigManager()
l4_config = config_manager.config

class UserModel(BaseModel):
    username: str
    password: str

     
'''
地图路径
'''
vpk_path = "left4dead2/addons"


PLAYERSDATA = Path() / "data/L4D2/image/players"
"""用户数据路径"""
TEXT_PATH = Path(__file__).parent / 'data/L4D2/image'
"""图片存储路径"""
TEXT_XPATH = Path() / 'data/L4D2/image'
"""内置图片路径"""



PLAYERSDATA = Path() / "data/L4D2/sql"
"""数据库路径"""
DATASQLITE = Path().parent / "data/L4D2/sql/L4D2.db"
"""数据库！"""  

table_data = ["L4d2_players","L4D2_server"]
"""数据库表"""
L4d2_players_tag = ['qq', 'nickname', 'steamid']
"""数据库表1"""
L4d2_server_tag = ['id','qqgroup', 'host', 'port', 'rcon']
"""数据库表2"""
L4d2_INTEGER = ['id','qq','qqgroup','port']
"""INITEGER的表头"""
L4d2_TEXT = ['nickname','steamid','host','rcon','path']
"""TEXT的表头"""
L4d2_BOOLEAN = ['use']
"""BOOLEAN的表头"""

tables_columns = {
    table_data[0]:L4d2_players_tag,
    table_data[1]:L4d2_server_tag
}

# 求生anne服务器
anne_url = "https://server.trygek.com/"

gamemode_list = [
    '纯净',
    '魔改战役',
    '多特',
    '魔改多特',
    '写专',
    '对抗',
    '魔改对抗',
    '药役',
    '药抗',
    '包抗',
    '绝境',
    '死专',
    'ast',
    '清道夫',
]

# 系统
if platform.system() == 'Windows':
    systems:str = 'win'
elif platform.system() == 'Linux':
    systems:str = 'linux'
else:
    systems:str = 'others'
ANNE_IP = {}


          