from nonebot import on_notice,on_command,on_regex
import re
from .config import Master


# 服务器
up = on_notice()
rename_vpk = on_regex(
        r"^求生地图\s*(\S+.*?)\s*(改|改名)?\s*(\S+.*?)\s*$",
    flags=  re.S,
    block= True,
    priority= 20,
    permission= Master,
)

find_vpk = on_command("l4_map",aliases={"求生地图","查看求生地图"},priority=25,block=True)
del_vpk = on_command("l4_del_map",aliases={"求生地图删除","地图删除"},priority=20,block=True,permission= Master)
rcon_to_server = on_command('rcon',aliases={"求生服务器指令","服务器指令","求生服务器控制台"},block=True,permission= Master)

# anne
anne_player = on_command('Ranne',aliases={"求生anne"},priority=25,block=True)
anne_server = on_command('anneip',aliases={'求生anne服务器','求生药役服务器'},priority=20,block=True)
steam_bind = on_command('Rbind',aliases={'steam绑定','求生绑定','anne绑定'},priority=20,block=True)
del_bind = on_command('del_bind',aliases={'steam解绑','求生解绑','anne解绑'},priority=20,block=True)


# 查询
queries = on_command('queries',aliases={'求生ip'},priority=20,block=True)