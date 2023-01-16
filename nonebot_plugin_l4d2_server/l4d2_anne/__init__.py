
from nonebot.log import logger

from ..config import l4_steamid
from ..seach import *
from ..l4d2_data.players import L4D2Player
from ..l4d2_image import out_png


    

s = L4D2Player()



def anne_html(name:str):
    """搜索里提取玩家信息，返回列表字典""" 
    data_title = anne_search(name)
    data = data_title[0]
    title = data_title[1]
    if len(data) ==0 or data[0] == "No Player found.":
        return {}
    data_list:list = []
    for i in data:
        i:BeautifulSoup
        Rank = i.find('td', {'data-title': 'Rank:'}).text.strip()
        player = i.find('td', {'data-title': 'Player:'}).text.strip()
        points = i.find('td', {'data-title': 'Points:'}).text.strip()
        country = i.find('img')['alt']
        playtime = i.find('td', {'data-title': 'Playtime:'}).text.strip()
        last_online = i.find('td', {'data-title': 'Last Online:'}).text.strip()
        onclick = i['onclick']
        steamid = onclick.split('=')[2].strip("'")
        play_json ={
            title[0]:Rank,
            title[1]:player,
            title[2]:points,
            title[3]:country,
            title[4]:playtime,
            title[5]:last_online,
            title[6]:steamid
        }
        data_list.append(play_json)
    logger.info("搜寻数据")
    return data_list

def anne_html_msg(data_list:list):
    """从搜索结果的字典列表中，返回发送信息"""
    mes = '搜索到以下玩家信息'
    for one in data_list:
        one:dict
        if l4_steamid:
            x = 7
        else:
            x = 6
        titles = list(one.keys())
        for i in range(x):
            mes += '\n' + str(titles[i]) + ':' + str(one[titles[i]])
        mes += '\n--------------------'    
    return mes


  
   
async def write_player(id,msg:str,nickname:str):
    """绑定用户"""
    # 判断是steam
    if msg.startswith('STEAM'):

        data_tuple = s._query_player_steamid(id)
        qq , nickname , steamid = data_tuple
        a = s._add_player_steamid(id , nickname , msg)
        print(a)
        if not a:
            return "出现未知错误"

        mes = '绑定成功喵~\nQQ:' + nickname +'\n' + 'steamid:'+msg
        return mes
    else:
        try:
            data_tuple = s._add_player_nickname(id,msg,None)
            qq , nickname , steamid = data_tuple
            s._add_player_steamid(id , msg , steamid)
        except TypeError:
            if not s._add_player_steamid(id , msg , None):
                return "出现未知错误"            
        mes = '绑定成功喵~\nQQ:' + nickname +'\n' + 'steam昵称:'+msg
        return mes

        

        
def del_player(id:str):
    """删除绑定信息,返回消息"""
    if not s._query_player(id):
        return '你还没有绑定过，请使用[求生绑定+昵称/steamid]'
    if s._delete_player:
        return '删除成功喵~'
        

    
async def id_to_mes(name:str):
    """根据name从数据库,返回steamid、或者空白"""
    data_tuple = s.search_data(None,name,None)
    if data_tuple:
        steamid = data_tuple[2]
        return steamid
    return None
    

def anne_rank_dict(name:str):
    """用steamid,查详情,输出字典"""
    data_dict = {}
    url =f'https://sb.trygek.com/l4d_stats/ranking/player.php?steamid={name}'
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    }
    data = httpx.get(url,headers=headers,timeout=30).content.decode('utf-8')
    data = BeautifulSoup(data, 'html.parser')
    detail = data.find_all('table')
    n = 0
    while n < 2:
        data_list = []
        detail2 = detail[n]
        tr = detail2.find_all('tr')
        for i in tr:
            title = i.find('td', {'class': 'w-50'})
            value = title.find_next_sibling('td')
            new_dict = {title.text:value.text}
            data_dict.update(new_dict)
        data_list.append(data_dict)
        n += 1
    return data_list

def anne_rank_dict_msg(data_list):
    """字典转msg"""
    msg = ''
    for data_dict in data_list:
        mes = ''
        for i in data_dict:
            mes +='\n'+ i + data_dict[i]
        mes += '\n--------------------'
        msg += mes
    return msg


async def anne_messgae(name:str,usr_id:str):
    """获取anne信息可输出信息"""
    if name:
        logger.info("关键词查询",name)
        if not name.startswith('STEAM'):
            steamid = await id_to_mes(name)
            if not steamid:
                logger.info("没有找到qq，使用默认头像")
                message = anne_html(name)
                usr_id = "1145149191810"
                if len(message) == 0:
                    return '没有叫这个名字的...'
                if len(message) > 1:
                    return anne_html_msg(message)
                name = message[0]['steamid']
            else:
                name = steamid
        # steamid
        msg = anne_rank_dict(name)[0]
        logger.info('使用图片')
        msg = await out_png(usr_id,msg)
        return msg
    else:
        """
        1、qq>数据>没有数据，返回
        2、qq>数据>steamid>查询
        3、qq>数据>昵称>查询
        """
        logger.info("qq信息查询")
        data_tuple = s._query_player_qq(usr_id)
        if not data_tuple:
            return "没有绑定信息..."
        # 只有名字，先查询数据在判断
        elif not data_tuple[2]:
            name = await id_to_mes(data_tuple[1])
            if not name:
                return f'未找到该玩家...'
            msg = anne_html(name)
            logger.info('有' + str(len(msg)) + '个信息')
            if str(len(msg)) !=1:
                logger.info('使用文字')
                msg = anne_html_msg(msg)
                return msg
            name = msg[0]['steamid']
        else:
            name = data_tuple[2]
        # name是steamid
        msg = anne_rank_dict(name)
        logger.info('使用图片')
        msg = msg[0]
        msg = await out_png(usr_id,msg)
        return msg