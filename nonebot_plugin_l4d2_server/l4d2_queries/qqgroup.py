from ..l4d2_data.serverip import L4D2Server
from ..l4d2_image import server_ip_pic
from . import queries,player_queries,player_queries_dict,queries_dict,player_queries_anne_dict
from nonebot.log import logger
import random
import time
from ..message import PRISON
si = L4D2Server()
    
async def get_qqgroup_ip_msg(qqgroup):
    """首先，获取qq群订阅数据，再依次queries返回ip原标"""
    ip_list = await si.query_server_ip(qqgroup)
    return ip_list
    
async def bind_group_ip(group:int,host:str,port:int):
    ip_list = await si.query_server_ip(group)
    if (host,port) in ip_list:
        return "本群已添加过该ip辣"
    await si.bind_server_ip(group,host,port)
    return "绑定成功喵，新增ip" + host

async def del_group_ip(group:int,number:int):
    number = int(number)
    logger.info(number)
    try:
        groups,host,port = await si.query_number(number)
    except TypeError:
        return '没有这个序号哦'
    if groups != group:
        return "本群可没有订阅过这个ip"
    await si.del_server_ip(number)
    return "取消成功喵，已删除序号" + str(number)
        
async def qq_ip_queries(msg:list[tuple]):
    """输入一个ip的二元元组组成的列表，返回一个输出消息的列表
    未来作图这里重置"""
    messsage = ""
    for i in msg:
        number,qqgroup,host,port = i
        msg2 = await player_queries(host,port)
        msg1 = await queries(host,port)
        messsage += '序号、'+ str(number) + '\n' + msg1 + msg2 + '--------------------\n'
    return messsage
            
async def qq_ip_queries_pic(msg:list[tuple]):
    """输入一个ip的四元元组组成的列表，返回一个输出消息的图片"""
    msg_list = []
    print(msg)
    for i in msg:
        number,qqgroup,host,port = i
        try:
            msg2 = await player_queries_anne_dict(host,port)
            msg1 = await queries_dict(host,port)
            msg1.update(msg2)
            msg1.update({'number':number})
            # msg1是一行数据完整的字典
            msg_list.append(msg1)
        except TypeError:
            pass
    pic = await server_ip_pic(msg_list)
    return pic
    
async def get_tan_jian(msg:list[tuple]):
    """获取探监列表"""
    msg_list = []
    rank = 0
    for i in msg:
        number,qqgroup,host,port = i 
        try:
            msg2 = await player_queries_anne_dict(host,port)
            point = 0
            for i in msg2['Players']:
                point += int(i['Score'])
            logger.info(point)
            if point/4 <50:
                logger.info('不够牢')
                continue
            else:
                msg1 = await queries_dict(host,port)
                if 'HT' in msg1['name']:
                    logger.info('HT训练忽略')
                    continue
                msg1.update(msg2)
                msg1.update({'ranks':point})
            # msg1是一行数据完整的字典
                msg_list.append(msg1)
        except (TypeError,KeyError):
            continue
    # 随机选一个牢房
    logger.info(len(msg_list))
    mse = random.choice(msg_list)
    message:str = ''
    ranks = mse['ranks']
    if ranks < 50 :
        return '暂时没有牢房'
    if 50 < ranks <= 120 :
        message = random.choice(PRISON[1])
    if 120 < ranks <= 200 :
        message = random.choice(PRISON[2])
    if ranks > 200 :
        message = random.choice(PRISON[3])       
    message += '\n' + '名称：' + mse['name'] + '\n'
    message += '地图：' + mse['map_'] + '\n'
    message += '玩家：' + mse['players'] + '/' + mse['max_players'] + '\n'
    n = 0
    for i in mse['Players']:
        n += 1 
        name = i['Name']
        Score = i['Score']
        Duration = i['Duration']
        s = str(n)
        message += f'{s}、{name} | {Score}分 |{Duration}\n'
    return message

async def get_server_ip(number):
    group,host,port = await si.query_number(number)
    try:
        return str(host) + ':' + str(port)
    except TypeError:
        return None