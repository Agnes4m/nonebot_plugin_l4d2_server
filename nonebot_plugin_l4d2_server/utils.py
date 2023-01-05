from zipfile import ZipFile
from nonebot.log import logger
import requests
import os
from pathlib import Path
from .image import txt_to_img
def get_file(url,down_file):
    '''
    下载指定Url到指定位置
    '''
    try:
        maps = requests.get(url)
        logger.info('已获取文件，尝试新建文件并写入')
        with open(down_file ,'wb') as mfile:
            mfile.write(maps.content)
            logger.info('下载成功')
            mes =('文件已下载,正在解压')
    except Exception as e:
        print(e)
        logger.info("文件获取不到/已损坏")
        mes = "寄"
    return mes

def get_vpk(vpk_list:list,path):
    '''
    获取所有vpk文件
    '''
    for file in os.listdir(path):
        if file.endswith('.vpk'):
            vpk_list.append(file)
    return vpk_list

def mes_list(mes,name_list:list):
    n = 0
    for i in name_list:
        n += 1
        mes += "\n" + str(n) + "、" + i
    return mes

def support_gbk(zip_file: ZipFile):
    '''
    中文恢复
    '''
    name_to_info = zip_file.NameToInfo
    # copy map first
    for name, info in name_to_info.copy().items():
        real_name = name.encode('cp437').decode('gbk')
        if real_name != name:
            info.filename = real_name
            del name_to_info[name]
            name_to_info[real_name] = info
    return zip_file

def del_map(num,map_path):
    '''
    删除指定的地图
    '''
    vpk_list = []
    map = get_vpk(vpk_list,map_path)
    map_name = map[int(num)-1]
    del_file = Path(map_path,map_name)
    os.remove(del_file)
    return map_name

def rename_map(num,rename,map_path):
    '''
    改名指定的地图
    '''
    vpk_list = []
    name = str(rename)
    map = get_vpk(vpk_list,map_path)
    map_name = map[int(num)-1]
    old_file = Path(map_path,map_name)
    new_file = Path(map_path,name)
    os.rename(old_file,new_file)
    logger.info('改名成功')
    return map_name

def text_to_png(msg: str) -> bytes:
    """文字转png"""
    return txt_to_img(msg)