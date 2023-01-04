import os
import zipfile
from nonebot import on_notice,on_command
from nonebot.adapters.onebot.v11 import NoticeEvent,Bot,MessageEvent
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.matcher import Matcher
import patoolib
from pathlib import Path
from time import sleep
from .config import *
from .utils import *
try:
    from nonebot.plugin import PluginMetadata
    __version__ = "0.0.8"
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


up = on_notice()
find_vpk = on_command("map",aliases={"求生地图","求生2地图"},priority=20,block=True)

@up.handle()
async def _(bot:Bot ,event: NoticeEvent, matcher: Matcher):
    # 检查下载路径是否存在
    if not Path(l4_file).exists():
        await up.finish("你填写的路径不存在辣")
    if not Path(map_path).exists():
        await up.finish("这个路径并不是求生服务器的路径，请再看看罢")
    # 这部分参考了gsuid
    args = event.dict()
    if args['notice_type'] != 'offline_file':
        await matcher.finish()
    url = args['file']['url']
    name: str = args['file']['name']
    user_id = args['user_id']
    # 如果不符合格式则忽略
    if not name.endswith(file_format):
        return
    await up.send('已收到压缩包，开始下载')
    sleep(1)   # 等待一秒防止因为文件名获取出现BUG
    
    down_file = Path(map_path,name)
    if get_file(url,down_file) == "寄":
        await up.finish("获取文件失败，可能文件已损坏")
    else:
        await up.send('文件已下载,正在解压')

    # 获取文件名
    zip_dir = os.path.dirname(down_file)
    original_vpk_files = []
    original_vpk_files = get_vpk(original_vpk_files,map_path)
    # 解压
    if zip_dir.endswith == ".zip":
        with zipfile.ZipFile(down_file, 'r') as zip_ref:
            zip_ref.extractall(zip_dir)
        os.remove(down_file)
    elif zip_dir.endswith == ".7z":
        patoolib.extract_archive(down_file,map_path)
        os.remove(down_file)
    elif zip_dir.endswith == ".vpk":
        pass
    extracted_vpk_files = []
    extracted_vpk_files = get_vpk(extracted_vpk_files,map_path)
    # 获取新增vpk文件的list
    vpk_files = list(set(extracted_vpk_files) - set(original_vpk_files))
    mes = "解压成功，新增以下几个vpk文件"
    await up.finish(mes_list(mes,vpk_files))
    
@find_vpk.handle()
async def _(bot:Bot,event: MessageEvent):    
    name_vpk = []
    name_vpk = get_vpk(name_vpk,map_path)
    logger.info("获取文件列表成功")
    mes = "当前服务器下有以下vpk文件"
    await up.finish(mes_list(mes,name_vpk))
