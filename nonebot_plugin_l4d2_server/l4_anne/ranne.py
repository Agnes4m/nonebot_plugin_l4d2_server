# coding=utf-8
# anne战绩查询
from ..utils.api.request import L4API


async def get_anne_rank_out(steamid: str):
    msg = await L4API.get_anne_playerdetail(steamid)
    if msg is None:
        return None
    return f"""电信anne查询结果：
    昵称：{msg['info']['name']}
    排名：{msg['detail']['rank']}
    分数：{msg['detail']["source"]}
    击杀：{msg['detail']["kills"]}
    爆头率：{msg['detail']["avg_source"]}
    时间：{msg['info']['playtime']}
    上次：{msg['info']['lasttime']}
    """
