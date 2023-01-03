import nonebot
import os
import zipfile
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import NoticeEvent,Bot
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.matcher import Matcher
import requests
from pathlib import Path
from time import sleep
try:
    from nonebot.plugin import PluginMetadata
    __version__ = "0.0.7"
    __plugin_meta__ = PluginMetadata(
        name="求生服务器操作",
        description='群内对服务器的简单操作',
        usage='求生服务器操作指令',
        extra={
            "version": __version__,
            "author": "Umamusume-Agnes-Digital <Z735803792@163.com>",
        },
    )
except:
    pass


# file 填写求生服务器所在路径
try:
    l4_file: str = nonebot.get_driver().config.l4d2_file
except:
    l4_file: str = '/home/ubuntu/l4d2/coop/left4dead2/addons'

up = on_notice()


@up.handle()
async def download(bot:Bot ,event: NoticeEvent, matcher: Matcher):
    # 这部分参考了gsuid
    args = event.dict()
    if args['notice_type'] != 'offline_file':
        await matcher.finish()
    url = args['file']['url']
    name: str = args['file']['name']
    user_id = args['user_id']
    if not name.endswith('.zip') and not name.endswith('.7z'):
        return
    await up.send('已收到压缩包，开始下载')
    sleep(1)
    print('已获取url')
    down_file = Path(l4_file,name)
    if not Path(l4_file).exists():
        os.makedirs(l4_file)
    print(down_file)
    try:
        print('尝试获取文件')
        maps = requests.get(url)
        print(type(maps))
        print('已获取文件，尝试新建文件并写入')
        with open(down_file ,'wb') as mfile:
            print('正在写入')
            mfile.write(maps.content)
            print('下载成功')
        await up.send('文件已下载,正在解压')
    except Exception as e:
        print(e)
        logger.info("文件获取不到/已损坏")
    
    zip_dir = os.path.dirname(down_file)

    # 解压
    with zipfile.ZipFile(down_file, 'r') as zip_ref:
        zip_ref.extractall(zip_dir)
        await up.send('解压成功')
    # 删除压缩包
    os.remove(down_file)
    
    import subprocess

    # Call the terminal and run the command "sh start.sh"
    subprocess.run("su - ubuntu; screen -r coop; exit();sh coop.sh", shell=True)

    import subprocess

