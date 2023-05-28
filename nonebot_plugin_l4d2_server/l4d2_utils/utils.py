
from nonebot.adapters.onebot.v11 import Bot,MessageEvent,GroupMessageEvent
from nonebot.log import logger
import struct
import httpx
import os
from pathlib import Path

from typing import List,Dict,Union,Optional
from .txt_to_img import txt_to_img
from .config import *
from ..l4d2_anne import write_player,del_player,anne_messgae
from ..l4d2_server.rcon import read_server_cfg_rcon,rcon_server
from ..l4d2_queries import queries,player_queries
from ..l4d2_queries.qqgroup import *
from ..l4d2_server.workshop import workshop_to_dict
from ..l4d2_image.steam import url_to_byte
import tempfile
import random



async def get_file(url: str, down_file: Path):
    '''
    下载指定Url到指定位置
    '''
    try:
        if l4_config.l4_only:
            maps = await url_to_byte(url)
        else:
            maps = httpx.get(url).content
        logger.info('已获取文件，尝试新建文件并写入')
        with open(down_file, 'wb') as mfile:
            mfile.write(maps)
        logger.info('下载成功')
        return '文件已下载，正在解压'
    except Exception as e:
        logger.info(f"文件获取不到/已损坏:原因是{e}")
        return None


def get_vpk(vpk_list: List[str], map_path: Path, file_: str = '.vpk') -> List[str]:
    '''
    获取路径下所有vpk文件名，并存入vpk_list列表中
    '''
    vpk_list.extend([file for file in os.listdir(str(map_path)) if file.endswith(file_)])
    return vpk_list



def mes_list(mes: str, name_list: List[str]) -> str:
    if name_list:
        for idx, name in enumerate(name_list):
            mes += f'\n{idx+1}、{name}'
    return mes




def del_map(num: int, map_path: Path) -> str:
    '''
    删除指定的地图
    '''
    map = get_vpk(map_path)
    map_name = map[num - 1]
    del_file = map_path / map_name
    os.remove(del_file)
    return map_name


def rename_map(num: int, rename: str, map_path: Path) -> str:
    '''
    改名指定的地图
    '''
    map = get_vpk(map_path)
    map_name = map[num - 1]
    old_file = map_path / map_name
    new_file = map_path / rename
    os.rename(old_file, new_file)
    logger.info('改名成功')
    return map_name


def text_to_png(msg: str) -> bytes:
    """文字转png"""
    return txt_to_img(msg)



def solve(msg:str):
    """删除str最后一行"""
    lines = msg.splitlines()
    lines.pop()
    return '\n'.join(lines)


async def search_anne(name:str,usr_id:str):
    """获取anne成绩"""
    return await anne_messgae(name,usr_id)
    

async def bind_steam(id:str,msg:str,nickname:str):
    """绑定qq-steam"""
    return await write_player(id,msg,nickname)

def name_exist(id:str):
    """删除绑定信息"""
    return del_player(id)

async def get_message_at(data: str) -> list:
    data = json.loads(data)
    return [int(msg['data']['qq']) for msg in data['message'] if msg['type'] == 'at']

    

def at_to_usrid(at):
    return at[0] if at else None


async def rcon_command(rcon, cmd):
    return await rcon_server(rcon, cmd.strip())

async def command_server(msg: str):
    rcon = await read_server_cfg_rcon()
    msg = await rcon_command(rcon, msg)
    if not msg:
        msg = '你可能发送了一个无用指令，或者换图导致服务器无响应'
    elif msg.startswith('Unknown command'):
        msg = '无效指令：' + msg.replace('Unknown command', '').strip()
    return msg.strip().replace('\n', '')




async def queries_server(msg:list) -> str:
    """查询ip返回信息"""
    ip = msg[0]
    port = msg[1]
    msgs = ''
    try:
        msgs = await  queries(ip,port)
        msgs += await player_queries(ip,port)
    except (struct.error,TimeoutError):
        pass
    # except Exception:
        # msgs = '有无法识别的用户名'
        # return msgs
    return msgs

async def add_ip(group_id,host,port):
    """先查找是否存在，如果不存在则创建"""
    return await bind_group_ip(group_id,host,port)

async def del_ip(group_id,number):
    """删除群ip"""
    return await del_group_ip(group_id,number)

async def show_ip(group_id):
    """先查找群ip，再根据群ip返回"""
    data_list = await get_qqgroup_ip_msg(group_id)
    logger.info(data_list)
    if len(data_list) == 0 :
        return "本群没有订阅"
    msg = await qq_ip_queries_pic(data_list)
    return  msg

async def get_number_url(number):
    'connect AGNES.DIGITAL.LINE.PM:40001'
    ip = await get_server_ip(number)
    if not ip:
        return '该序号不存在'
    url = f'connect {ip}'
    return url

async def workshop_msg(msg:str):
    """url变成id，拼接post请求"""
    if msg.startswith('https://steamcommunity.com/sharedfiles/filedetails/?id'):
        try:
            msg = msg.split('&')[0]
        except:
            pass
        msg = msg.replace('https://steamcommunity.com/sharedfiles/filedetails/?id=','')
    if msg.isdigit():
        data:Union[dict,List[dict]] = await workshop_to_dict(msg)
        return data
    else:
        return None
    
async def save_file(file:bytes,path_name):
    """保存文件"""
    with open(path_name,'w') as files:
        files.write(file)
        
async def get_anne_server_ip(ip ,ismsg :bool = False):
    """输出查询ip和ping"""
    host,port = split_maohao(ip)
    data = await queries_server([host,port])
    lines = data.splitlines()
    msg = '\n'.join(lines[1:])
    msg += '\nconnect ' + ip
    return msg

async def upload_file(bot: Bot, event: MessageEvent, file_data: bytes, filename: str):
    """上传临时文件"""
    if systems == "win" or "other":
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(Path(temp_dir) / filename, "wb") as f:
                f.write(file_data)
            if isinstance(event, GroupMessageEvent):
                await bot.call_api(
                    "upload_group_file", group_id=event.group_id, file=f.name, name=filename
                )
            else:
                await bot.call_api(
                    "upload_private_file", user_id=event.user_id, file=f.name, name=filename
                )
        os.remove(Path().joinpath(filename))
    elif systems == "linux":
        with tempfile.NamedTemporaryFile("wb+") as f:
            f.write(file_data)
            if isinstance(event, GroupMessageEvent):
                await bot.call_api(
                    "upload_group_file", group_id=event.group_id, file=f.name, name=filename
                )
            else:
                await bot.call_api(
                    "upload_private_file", user_id=event.user_id, file=f.name, name=filename
                )


async def json_server_to_tag_dict(key:str,msg:str):
    """
    l4d2字典转tag的dict结果
     - 1、先匹配腐竹
     - 2、再匹配模式、没有参数则从直接匹配最上面的
     - 3、匹配数字（几服），没有参数则从结果里随机返回一个
    """
    data_dict = {}
    data_list = []
    msg = msg.replace(' ','')
    # 腐竹循环
    for tag,value in ALL_HOST.items():
        value:List[dict]  
        if tag == key:
            data_dict.update({'server':tag})
            if not msg:
                # 腐竹
                data_dict.update(random.choice(value))
            elif msg.isdigit():
                logger.info("腐竹 + 序号")
                for server in value:
                    if msg == str(server['id']):
                        data_dict.update(server)
                        break
            else:
                logger.info("腐竹 + 模式 + 序号")
                for server in value:
                    if msg.startswith(server['version']):
                        data_list.append(server)
                        msg_id = msg[len(server['version']):]
                        if msg_id == str(server['id']):
                            data_dict.update(server)
                            break
                else:
                    # 腐竹 + 模式
                    data_dict.update(random.choice(data_list))

    logger.info(data_dict)
    return data_dict



sub_menus = []

def register_menu_func(
    func: str,
    trigger_condition: str,
    brief_des: str,
    trigger_method: str = '指令',
    detail_des: Optional[str] = None,
):
    sub_menus.append(
        {
            'func': func,
            'trigger_method': trigger_method,
            'trigger_condition': trigger_condition,
            'brief_des': brief_des,
            'detail_des': detail_des or brief_des,
        }
    )

def register_menu(*args, **kwargs):
    def decorator(f):
        register_menu_func(*args, **kwargs)
        return f

    return decorator


async def extract_last_digit(msg: str) -> tuple[str, str]:
    "分离str和数字"
    for i in range(len(msg) - 1, -1, -1):
        if msg[i].isdigit():
            last_digit = msg[i]
            new_msg = msg[:i]
            return new_msg, last_digit
    return msg, ''