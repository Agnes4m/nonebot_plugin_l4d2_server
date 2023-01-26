from VSQ import l4d2

async def queries(ip:str,port:int):
    port = int(port)
    msg_dict = await queries_dict(ip,port)
    message = 'ip:' + msg_dict['ip'] + '\n'
    message += '名称：' + msg_dict['name'] + '\n'
    message += '地图：' + msg_dict['map_'] + '\n'
    message += '玩家：' + msg_dict['players'] + '/' + msg_dict['max_players'] + '\n'
    return message

async def queries_dict(ip:str,port:int) -> dict:
    port = int(port)
    msg_dict = {}
    message_dict = await l4d2.server(ip,port,times=5)
    msg_dict['folder'] =  message_dict['folder']
    msg_dict['name'] =  message_dict['name']
    msg_dict['map_'] =  message_dict['map_']
    msg_dict['players'] =  message_dict['players']
    msg_dict['max_players'] =  message_dict['max_players']
    msg_dict['ip'] = str(ip) + ':' +str(port)
    return msg_dict
    
async def player_queries_anne_dict(ip:str,port:int): 
    """anne算法返回玩家"""
    port = int(port)
    message_dic = await l4d2.APlayer(ip,port,times=5)
    if message_dic == {}:
        message_dic['header'] = 0
    else:
        pass
        # new_list = []
        # for i in message_dic['Players']:
        #     new_list.append(i['Name'])
        # new_dict.update({'Players':new_list})
    return message_dic

async def player_queries_dict(ip:str,port:int): 
    """一般算法返回玩家"""
    port = int(port)
    new_dict = {}
    message_dic = await l4d2.APlayer(ip,port,times=5)
    if message_dic == {}:
        new_dict['header'] = 0
    else:
        pass
        new_list = []
        for i in message_dic['Players']:
            new_list.append(i['Name'])
        new_dict.update({'Players':new_list})
    return new_dict

async def player_queries(ip:str,port:int): 
    port = int(port)
    message_dic = await player_queries_anne_dict(ip,port)
    n = 0
    # message:str = '玩家数量：' + message_dic['header'] + '\n'
    message = ''
    for i in message_dic['Players']:
        n += 1 
        name = i['Name']
        Score = i['Score']
        Duration = i['Duration']
        s = str(n)
        message += f'{s}、{name} | {Score}分 |{Duration}\n'
    return message

async def player_queries_dict(ip:str,port:int): 
    port = int(port)
    message_dic = await player_queries_dict(ip,port)
    n = 0
    # message:str = '玩家数量：' + message_dic['header'] + '\n'
    message = ''
    for i in message_dic['Players']:
        n += 1 
        name = i['Name']
        Duration = i['Duration']
        s = str(n)
        message += f'{s}、{name} |{Duration}\n'
    return message