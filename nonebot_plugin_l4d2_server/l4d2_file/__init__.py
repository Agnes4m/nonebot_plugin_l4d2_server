from pathlib import Path
from zipfile import ZipFile
from time import sleep
import sys
import os
from ..utils import get_file,get_vpk
from ..config import map_path
from nonebot.log import logger
from py7zr import SevenZipFile
from rarfile import RarFile



async def updown_l4d2_vpk(map_path,name,url):
    """从url下载压缩包并解压到位置"""
    original_vpk_files = []
    original_vpk_files = get_vpk(original_vpk_files,map_path)
    down_file = Path(map_path,name)
    if await get_file(url,down_file) == None:
        return None
    sleep(1)
    msg = open_packet(name,down_file)
    logger.info(msg)
    
    sleep(1)
    extracted_vpk_files = []
    extracted_vpk_files = get_vpk(extracted_vpk_files,map_path)
    logger.info(extracted_vpk_files)
    # 获取新增vpk文件的list
    vpk_files = list(set(extracted_vpk_files) - set(original_vpk_files))
    return  vpk_files

def open_packet(name:str,down_file:Path):
    """解压压缩包"""
    zip_dir = os.path.dirname(down_file)
    logger.info('文件名为：' + name)
    if name.endswith('.zip'):
        mes = 'zip文件已下载,正在解压'
        with support_gbk(ZipFile(down_file, 'r')) as z:
            z.extractall(zip_dir)
        os.remove(down_file)
    elif name.endswith('.7z'):
        mes ='7z文件已下载,正在解压'
        with support_gbk(SevenZipFile(down_file, 'r')) as z:
            z.extractall(zip_dir)
        os.remove(down_file)
    elif name.endswith('rar'):
        mes = 'rar文件已下载,正在解压'
        with support_gbk(RarFile(down_file,'r')) as z:
            z.extractall(zip_dir)
        os.remove(down_file)
    elif name.endswith('.vpk'):
        mes ='vpk文件已下载'
    return mes

def support_gbk(zip_file):
    '''
    压缩包中文恢复
    '''
    if type(zip_file) == ZipFile:
        name_to_info = zip_file.NameToInfo
        # copy map first
        for name, info in name_to_info.copy().items():
            real_name = name.encode('cp437').decode('gbk')
            if real_name != name:
                info.filename = real_name
                del name_to_info[name]
                name_to_info[real_name] = info
    elif type(zip_file) == RarFile:
        rar_file = zip_file
        name_to_info = {info.filename: info for info in rar_file.infolist()}
        for name, info in name_to_info.copy().items():
            real_name = name.encode(sys.getfilesystemencoding(), errors='ignore').decode('gbk')
            if real_name != name:
                info.filename = real_name
                del name_to_info[name]
                name_to_info[real_name] = info
                zip_file = rar_file
    return zip_file