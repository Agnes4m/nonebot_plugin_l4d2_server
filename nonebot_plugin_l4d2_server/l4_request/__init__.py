from typing import Dict, List, Optional, cast

from nonebot.log import logger

from ..config import server_all_path
from ..l4_image import msg_to_image
from ..utils.api.models import NserverOut
from ..utils.utils import split_maohao
from .draw_msg import draw_one_ip, get_much_server

try:
    import ujson as json
except ImportError:
    import json


# 获取全部服务器信息
ALLHOST: Dict[str, List[NserverOut]] = {}
COMMAND = set()


async def get_server_detail(
    command: str,
    _id: Optional[str] = None,
    is_img: bool = True,
):
    server_json = ALLHOST.get(command)
    logger.info(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    if _id is None:
        # 输出组信息
        logger.info("正在请求组服务器信息")
        server_dict = await get_much_server(server_json, command)
        if is_img:
            return await msg_to_image(server_dict)
        return server_dict

    # 返回单个
    logger.info("正在请求单服务器信息")
    for i in server_json:
        if _id == i["id"]:
            return await draw_one_ip(i["host"], i["port"])
    return None


async def get_ip_server(ip: str):
    host, port = split_maohao(ip)
    return await draw_one_ip(host, port)


# 以下是重载ip
def reload_ip():
    for item in server_all_path.iterdir():
        if item.is_file():
            if item.name.endswith("json"):
                json_data = json.loads(item.read_text(encoding="utf-8"))
                group_server = cast(Dict[str, List[NserverOut]], json_data)

                for group, group_ip in group_server.items():
                    # 处理ip,host,port关系
                    for one_ip in group_ip:
                        if one_ip.get("ip"):
                            if one_ip.get("host") and one_ip.get("port"):
                                pass
                            if one_ip.get("host") and not one_ip.get("port"):
                                one_ip["port"] = 20715
                            if not one_ip.get("host"):
                                one_ip["host"], one_ip["port"] = split_maohao(
                                    one_ip.get("ip"),
                                )
                        else:
                            if one_ip.get("host") and one_ip.get("port"):
                                one_ip["ip"] = f'{one_ip["host"]}:{one_ip["port"]}'
                            if one_ip.get("host") and not one_ip.get("port"):
                                one_ip["ip"] = f'{one_ip["host"]}:20715'
                            else:
                                logger.warning(f"{one_ip} 没有ip")

                    ALLHOST.update({group: group_ip})
                    COMMAND.add(group)
                logger.success(f"成功加载 {item.name.split('.')[0]} {len(group_ip)}个")

            if item.name.endswith("txt"):
                """to do"""


reload_ip()
