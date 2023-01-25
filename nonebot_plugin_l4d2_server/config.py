import nonebot
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)
from pathlib import Path
try:
    import ujson as json
except:
    import json
    
file_format = (".vpk",".zip",".7z")
Master = SUPERUSER | GROUP_ADMIN | GROUP_OWNER 
# file 填写求生服务器所在路径
FONT_ORIGIN_PATH = Path(__file__).parent / 'data/L4D2/font.ttf'
try:
    l4_file: str = nonebot.get_driver().config.l4_file
except:
    l4_file: str = '/home/ubuntu/l4d2/coop'

try:
    l4_image: bool = nonebot.get_driver().config.l4_image
except:
    l4_image: bool = True

try:
    l4_steamid: bool = nonebot.get_driver().config.l4_steamid
except:
    l4_steamid: bool = True
    
try:
    l4_font: str = nonebot.get_driver().config.l4_font
except:
    l4_font: str = str(FONT_ORIGIN_PATH)
     
try:
    l4_host: str = nonebot.get_driver().config.l4_host
except:
    l4_host: str = '127.0.0.1'
    
try:
    l4_port: int = nonebot.get_driver().config.l4_port
except:
    l4_port: int = 20715

try:
    l4_rcon: str = nonebot.get_driver().config.l4_rcon
except:
    l4_rcon: str = '114514'
try:
    l4_proxies: str = {
            'http://':nonebot.get_driver().config.l4_proxies
        }
except:
    l4_proxies = ''
# 文件路径
vpk_path = "left4dead2/addons"
cfg_server = Path(l4_file,'left4dead2/cfg/server.cfg')
map_path = Path(l4_file,vpk_path)
'''
地图路径
'''

PLAYERSDATA = Path() / "data/L4D2/image/players"
"""用户数据路径"""
TEXT_PATH = Path(__file__).parent / 'data/L4D2/image'
"""图片存储路径"""
TEXT_XPATH = Path().parent / 'data/L4D2/image'
"""内置图片路径"""



DATASQLITE = Path(__file__).parent / "data/L4D2/sql"
"""数据库路径"""
datasqlite = Path(__file__).parent / "data/L4D2/sql/L4D2.db"
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

