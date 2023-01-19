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
    
async def player_queries_dict(ip:str,port:int): 
    port = int(port)
    message_dic = await l4d2.APlayer(ip,port,times=5)
    new_dict = {}
    if message_dic == {}:
        new_dict['header'] = 0
    else:
        new_list = []
        for i in message_dic['Players']:
            new_list.append(i['Name'])
        new_dict.update({'Players':new_list})
    return new_dict

async def player_queries(ip:str,port:int): 
    port = int(port)
    message_dic = player_queries_dict(ip,port)
    n = 0
    message = '玩家数量：' + message_dic['header'] + '\n'
    for i in message_dic['Players']:
        n += 1 
        message += str(n) + '、' + str(i) +'\n'
    return message
