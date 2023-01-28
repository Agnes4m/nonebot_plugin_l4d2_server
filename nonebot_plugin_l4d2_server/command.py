from nonebot import on_notice,on_command,on_regex,on_fullmatch
import re
from .l4d2_anne.server import ANNE_IP
from .config import Master

help_ = on_command('l4_help',aliases={'求生帮助'},priority=20,block=True)

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
anne_bind = on_command('Rbind',aliases={'steam绑定','求生绑定','anne绑定'},priority=20,block=True)
del_bind = on_command('del_bind',aliases={'steam解绑','求生解绑','anne解绑'},priority=20,block=True)
read_ip = on_command('anne',aliases={'求生云服'},priority=20,block=True)
updata = on_command('updata',aliases={'求生更新云服'},priority=20,block=True,permission= Master)

# keys = ANNE_IP.keys()
# get_ip = on_command('114514919181',set(keys),priority=80)
    
get_anne = on_command('云',priority=20,block=True)
tan_jian = on_command('tj',aliases={'探监'},priority=20,block=True)

# 查询
queries = on_command('queries',aliases={'求生ip'},priority=20,block=True)
add_queries = on_command('addq',aliases={"求生添加订阅"},priority=20,block=True,permission= Master)
del_queries = on_command('delq',aliases={"求生取消订阅"},priority=20,block=True,permission= Master)
show_queries = on_command('showq',aliases={"求生订阅"},priority=20,block=True)
join_server = on_command('showq',aliases={"求生加入"},priority=20,block=True)

# 下载内容
up_workshop = on_command('workshop',aliases={'创意工坊下载','求生创意工坊'},priority=20,block=True)


@help_.handle()
async def _():
    msg = [
        '=====求生机器人帮助=====',
        '1、电信服战绩查询【求生anne[id/steamid/@]】',
        '2、电信服绑定【求生绑定[id/steamid]】',
        '3、电信服状态查询【云xx】'
        '4、创意工坊下载【创意工坊下载[物品id/链接]】',
        '5、指定ip查询【求生ip[ip]】(可以是域名)',
        '6、本地服务器操作(略，详情看项目地址)',
    ]
    messgae = ''
    for i in msg:
        messgae += i + '\n'
    await help_.finish(messgae)