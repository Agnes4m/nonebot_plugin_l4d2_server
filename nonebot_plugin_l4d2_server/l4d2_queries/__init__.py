import a2s
from typing import List

async def queries(ip:str,port:int):
    port = int(port)
    msg_dict = await queries_dict(ip,port)
    message = 'ip:' + msg_dict['ip'] + '\n'
    message += '名称：' + msg_dict['name'] + '\n'
    message += f"地图：{msg_dict['map_']}\n"
    message += f"延迟：{msg_dict['ping']}\n"
    message += f"玩家：{msg_dict['players']} / {msg_dict['max_players']}\n"
    return message

async def queries_dict(ip:str,port:int) -> dict:
    port = int(port)
    ip = str(ip)
    msg_dict = {}
    # message_dict = await l4d(ip,port)
    msg:a2s.SourceInfo = await a2s.ainfo((ip,port))
    msg_dict['folder'] =  msg.folder
    msg_dict['name'] =  msg.server_name
    msg_dict['map_'] =  msg.map_name
    msg_dict['players'] =  msg.player_count
    msg_dict['max_players'] =  msg.max_players
    msg_dict['rank_players'] =  f'{msg.player_count}/{msg.max_players}'
    msg_dict['ip'] = str(ip) + ':' +str(port)
    msg_dict['ping'] = f"{msg.ping*1000:.0f}ms"
    msg_dict['system'] =  f"{msg.platform}.svg"
    if msg_dict['players'] < msg_dict['max_players']:
        msg_dict['enabled'] = True
    else:
        msg_dict['enabled'] = False
    return msg_dict
    
async def player_queries_anne_dict(ip:str,port:int): 
    """anne算法返回玩家"""
    port = int(port)
    # message_dic = await l4d2.APlayer(ip,port,times=5)
    message_list:List[a2s.Player] = await a2s.aplayers((ip,port))
    msg_list = []
    if message_list != []:
        for i in message_list:
            msg_list.append({
                'name':i.name,
                'Score':i.score,
                'Duration':await convert_duration(i.duration)
            })
    return msg_list

# async def player_queries_dict(ip:str,port:int): 
#     """一般算法返回玩家"""
#     port = int(port)
#     new_dict = {}
#     message_dic = await l4d2.APlayer(ip,port,times=5)
#     if message_dic == {}:
#         new_dict['header'] = 0
#     else:
#         pass
#         new_list = []
#         for i in message_dic['Players']:
#             new_list.append(i['Name'])
#         new_dict.update({'Players':new_list})
#     return new_dict

async def player_queries(ip:str,port:int): 
    port = int(port)
    message_list = await player_queries_anne_dict(ip,port)
    return await msg_ip_to_list(message_list)

async def msg_ip_to_list(message_list:list):
    message = ''
    n = 0
    if message_list == []:
        message += '服务器里，是空空的呢\n'
    else:
        max_duration_len = max([len(str(i['Duration'])) for i in message_list])
        max_score_len = max([len(str(i['Score'])) for i in message_list])
        for i in message_list:
            print(i)
            n += 1 
            name = i['name']
            Score = i['Score']
            if Score == '0':
                Score = '摸'
            Duration = i['Duration']
            soc = "[{:>{}}]".format(Score,max_score_len)
            dur = "{:^{}}".format(Duration, max_duration_len)
            message += f'{soc} | {dur} | {name} \n'
    return message

async def convert_duration(duration: int) -> str:
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    time_str = ""
    if hours > 0:
        time_str += f"{int(hours)}h "
    if minutes > 0 or hours > 0:
        time_str += f"{int(minutes)}m "
    time_str += f"{int(seconds)}s"
    return time_str.strip()

async def server_rule_dict(ip:str,port:int): 
    port = int(port)
    ip = str(ip)
    msg_dict = {}
    # message_dict = await l4d(ip,port)
    try:
        msg:dict = await a2s.arules((ip,port))
        msg_dict['tick'] = msg['l4d2_tickrate_enabler'] + "tick"
    except:
        msg_dict['tick'] = ''
    return msg_dict

