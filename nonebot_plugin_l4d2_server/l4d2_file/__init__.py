from pathlib import Path
from ..utils import get_file,get_vpk,open_packet
from nonebot.log import logger
from time import sleep

async def updown_l4d2_vpk(map_path,name,url):
    """从url下载压缩包并解压到位置"""
    original_vpk_files = []
    original_vpk_files = get_vpk(original_vpk_files,map_path)
    down_file = Path(map_path,name)
    if await get_file(url,down_file) == None:
        return None

    msg = open_packet(name,down_file)
    logger.info(msg)
    
    sleep(1)
    extracted_vpk_files = []
    extracted_vpk_files = get_vpk(extracted_vpk_files,map_path)
    logger.info(extracted_vpk_files)
    # 获取新增vpk文件的list
    vpk_files = list(set(extracted_vpk_files) - set(original_vpk_files))
    return  vpk_files