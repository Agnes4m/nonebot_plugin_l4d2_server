import nonebot
from pathlib import Path

file_format = (".vpk",".zip",".7z")
# file 填写求生服务器所在路径
try:
    l4_file: str = nonebot.get_driver().config.l4_file
except:
    l4_file: str = '/home/ubuntu/l4d2/coop'

# 文件路径
vpk_path = "left4dead2/addons"
map_path = Path(l4_file,vpk_path)
