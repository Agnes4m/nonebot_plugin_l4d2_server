from pathlib import Path
from zipfile import ZipFile
from time import sleep
import sys
import os
import io
from typing import List

from ..l4d2_utils.utils import get_file,get_vpk
from ..l4d2_utils.config import systems
from nonebot.log import logger
from rarfile import RarFile
import rarfile
from pyunpack import Archive



async def updown_l4d2_vpk(map_paths,name,url):
    """从url下载压缩包并解压到位置"""
    original_vpk_files = []
    original_vpk_files = get_vpk(original_vpk_files,map_paths)
    down_file = Path(map_paths,name)
    if await get_file(url,down_file) == None:
        return None
    sleep(1)
    msg = open_packet(name,down_file)
    logger.info(msg)
    
    sleep(1)
    extracted_vpk_files = []
    extracted_vpk_files = get_vpk(extracted_vpk_files,map_paths)
    # 获取新增vpk文件的list
    vpk_files = list(set(extracted_vpk_files) - set(original_vpk_files))
    return  vpk_files

def open_packet(name:str,down_file:Path):
    """解压压缩包"""
    down_path = os.path.dirname(down_file)
    logger.info('文件名为：' + name)
    logger.info(f'系统为{systems}')
    if systems == 'win':
        if name.endswith('.zip'):
            mes = 'zip文件已下载,正在解压'
            try:
                with support_gbk(ZipFile(down_file, 'r')) as z:
                    z.extractall(down_path)
            except UnicodeEncodeError:
                with ZipFile(down_file, 'r') as z:
                    z.extractall(down_path)                
            os.remove(down_file)
        elif name.endswith('.7z'):
            mes ='7z文件已下载,正在解压'
            Archive(down_file).extractall(down_path)
            # with SevenZipFile(down_file, 'r') as z:
            #     z.extractall(down_path)
            os.remove(down_file)
        elif name.endswith('rar'):
            mes = 'rar文件已下载,正在解压'
            with RarFile(down_file,'r') as z:
                z.extractall(down_path)
            os.remove(down_file)
        elif name.endswith('.vpk'):
            mes ='vpk文件已下载'
    else:
        if name.endswith('.zip'):
            mes = 'zip文件已下载,正在解压'
            with support_gbk(ZipFile(down_file, 'r')) as z:
                z.extractall(down_path)
            os.remove(down_file)
        elif name.endswith('.7z'):
            mes ='7z文件已下载,正在解压'
            Archive(down_file).extractall(down_path)
            # with SevenZipFile(down_file, 'r') as z:
            #     z.extractall(down_path)
            os.remove(down_file)
        elif name.endswith('rar'):
            mes = 'rar文件已下载,正在解压'
            with rarfile.RarFile(down_file,'r') as z:
                z.extractall(down_path)
            os.remove(down_file)
        else:
            mes ='vpk文件已下载'        
    return mes

def support_gbk(zip_file:ZipFile):
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
    return zip_file




async def all_zip_to_one(data_list:List[bytes]):
    """多压缩包文件合并"""
    file_list = []
    for data in data_list:
        # 将每个bytes对象解压缩成文件对象
        # 将文件对象存储在一个列表中
        file_list.append(io.BytesIO(data))

    # 创建一个新的BytesIO对象
    data_file = io.BytesIO()

    # 使用zipfile将列表中的文件对象添加到zipfile中
    with ZipFile(data_file, mode='w') as zf:
        for i, file in enumerate(file_list):
            # 将文件名设置为"file{i}.zip"，i为文件在列表中的索引
            filename = f"file{i}.zip"
            zf.writestr(filename, file.getvalue())

    # 获取zipfile的bytes对象
    return data_file.getvalue()
