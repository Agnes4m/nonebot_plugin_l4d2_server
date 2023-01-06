import nonebot
from pathlib import Path

file_format = (".vpk",".zip",".7z")
# file 填写求生服务器所在路径
try:
    l4_file: str = nonebot.get_driver().config.l4_file
except:
    l4_file: str = '/home/ubuntu/l4d2/coop'

try:
    l4_image: bool = nonebot.get_driver().config.l4_image
except:
    l4_image: bool = False

try:
    l4_steamid: bool = nonebot.get_driver().config.l4_steamid
except:
    l4_steamid: bool = False
# 文件路径
vpk_path = "left4dead2/addons"
map_path = Path(l4_file,vpk_path)
'''
地图路径
'''