from ..l4d2_data.serverip import L4D2Server
from . import queries,player_queries


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
        
async def qq_ip_queries(msg:list[tuple]):
    """输入一个ip的二元元组组成的列表，返回一个输出消息的列表
    未来作图这里重置"""
    messsage = ""
    for i in msg:
        print(i)
        qqgroup,host,port = i
        msg2 = await player_queries(host,port)
        msg1 = await queries(host,port)
        messsage += msg1 + msg2 + '\n--------------------\n'
    return messsage
            
        
    