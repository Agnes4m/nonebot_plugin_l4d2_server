from zipfile import ZipFile
from nonebot.log import logger
import httpx
import re
import os
try:
    import py7zr
except:
    pass
from pathlib import Path
from .txt_to_img import txt_to_img
from .config import *
from .l4d2_anne.__init__ import *
from .chrome import get_anne_server
from .l4d2_server.rcon import read_server_cfg_rcon,rcon_server
from .l4d2_image.draw_user_info import draw_user_info_img
from .l4d2_queries import queries

def get_file(url,down_file):
    '''
    下载指定Url到指定位置
    '''
    try:
        maps = httpx.get(url)
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
    压缩包中文恢复
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

def open_packet(name,down_file):
    """解压压缩包"""
    zip_dir = os.path.dirname(down_file)
    logger.info('文件名为：' + name)
    if name.endswith('.zip'):
        mes = 'zip文件已下载,正在解压'
        with support_gbk(ZipFile(down_file, 'r')) as zip_ref:
            zip_ref.extractall(zip_dir)
        os.remove(down_file)
    elif name.endswith('.7z'):
        mes ='7z文件已下载,正在解压'
        with py7zr.SevenZipFile(down_file, 'r') as z:
            z.extractall(map_path)
        os.remove(down_file)
    elif name.endswith('.vpk'):
        mes ='vpk文件已下载'
    return mes

def solve(s):
    """删除str最后一行"""
    s = s.split('\n', 1)[-1]
    if s.find('\n') == -1:
        return ''
    return s.rsplit('\n', 1)[0]

async def search_anne(name:str,usr_id:str):
    """qq为基础，获取anne信息可输出信息"""
    a = '详情'
    if any(word in name for word in a):
        logger.info('正在查询更多信息')
        name = name.replace(a,'')
        name = await id_to_mes(name,usr_id)
        if len(name)== 0:
            return '绑定信息不存在，或已失效'
        msg_list_dict = anne_rank_dice(name)
        msg = anne_rank_dict_msg(msg_list_dict)
    else:
        name = await id_to_mes(name,usr_id)
        if len(name)== 0:
            return '绑定信息不存在，或已失效'
        msg:list = anne_html(name)
        if len(msg)==0:
            return '未找到玩家...'
        logger.info('有' + str(len(msg)) + '个信息')
        logger.info(msg)
        # 如果只有一个字典，就输出图片
        if len(msg)== 1:
            logger.info('使用图片')
            msg = msg[0]
            msg = await draw_user_info_img(usr_id,msg)
            return msg
        else:
            logger.info('使用文字')
            msg = anne_html_msg(msg)
            msg = solve(msg)
            return msg
    

def bind_steam(id:str,msg:str,nickname:str):
    """绑定qq-steam"""
    return write_player(id,msg,nickname)

def name_exist(id:str):
    """删除绑定信息"""
    return del_player(id)

async def get_message_at(data: str) -> list:
    '''
    获取at列表
    :param data: event.json()
    抄的groupmate_waifu
    '''
    qq_list = []
    data = json.loads(data)
    try:
        for msg in data['message']:
            if msg['type'] == 'at':
                qq_list.append(int(msg['data']['qq']))
        return qq_list
    except Exception:
        return []
    
def anne_servers():
    mes = get_anne_server()
    mes = solve(mes)
    return mes

def at_to_usrid(usr_id,at):
    """at对象变qqid否则返回usr_id"""
    if at != []:
        if at and at[0] != usr_id:
            at = at[0]
        usr_id = at
    return usr_id

async def command_server(msg:str):
    """rcon控制台返回信息"""
    logger.info(cfg_server)
    rcon = await read_server_cfg_rcon()
    logger.info([msg,l4_host,l4_port,rcon])
    msg = await rcon_server(rcon,msg)
    logger.info(msg)
    if len(msg)==0:
        msg = '你可能发送了一个无用指令，或者换图导致服务器无响应'
    if msg.startswith('Unknown command'):
        msg = msg.replace('Unknown command','').strip()
        msg = '无效指令：' + msg
    msg = msg.strip()
    return msg

def split_maohao(msg:str) -> list:
    """分割大小写冒号"""
    msg:list = re.split(":|：",msg.strip())
    msg[-1] = msg[-1] if len(msg[-1])!=0 else '20715'  
    return msg

def queries_server(msg:list) -> str:
    print(msg)
    return queries(msg[0],msg[1])