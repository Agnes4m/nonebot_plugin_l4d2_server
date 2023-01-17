from VSQ import l4d2

async def queries(ip:str,port:int):
    port = int(port)
    message_dict = l4d2.server(ip,port,times=5)
    message = '游戏：' + message_dict['folder'] + '\n'
    message += '名称：' + message_dict['name'] + '\n'
    message += '地图：' + message_dict['map_'] + '\n'
    message += '玩家：' + message_dict['players'] + '/' + message_dict['max_players'] + '\n'
    return message

async def player_queries(ip:str,port:int): 
    port = int(port)
    message_dic = await l4d2.APlayer(ip,port,times=5)
    print(message_dic)
    n = 0
    message = '玩家数量：' + message_dic['header'] + '\n'
    for i in message_dic['Players']:
        n += 1 
        print(i)
        message += str(n) + '、' + str(i['Name']) +'\n'
    return message