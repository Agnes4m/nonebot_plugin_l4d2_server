from VSQ import l4d2

def queries(ip:str,port:int):
    port = int(port)
    message_dict = l4d2.get_server_info(ip,port,times=60)
    message = '服务器游戏：' + message_dict['folder'] + '\n'
    message += '服务器名称：' + message_dict['name'] + '\n'
    message += '地图：' + message_dict['map_'] + '\n'
    message += '玩家：' + message_dict['players'] + '/' + message_dict['max_players'] + '\n'
    message += 'VAC：' + '开启' if message_dict['vac'] else '关闭' + '\n'
    return message