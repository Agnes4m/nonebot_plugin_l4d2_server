from pathlib import Path
from typing import Dict, List, Tuple, cast

from nonebot.log import logger

from ..config import server_all_path
from ..utils.api.models import NserverDetail, NserverOut
from ..utils.utils import split_maohao

try:
    import ujson as json
except ImportError:
    import json


# 获取全部服务器信息
ALLHOST: Dict[str, List[NserverOut]] = {}
COMMAND = set()

def reload_ip():
    for item in server_all_path.iterdir():  
        if item.is_file():  
            if item.name.endswith("json"):
                json_data = json.loads(item.read_text(encoding="utf-8"))
                group_server = cast(Dict[str, List[NserverOut]],json_data)

                for group, group_ip in group_server.items():
                    # 处理ip,host,port关系
                    for one_ip in group_ip:
                        if one_ip.get("ip"):
                            if one_ip.get("host") and one_ip.get("port"):
                                pass
                            if one_ip.get("host") and not one_ip.get("port"):
                                one_ip["port"] == 20715
                            if not one_ip.get("host"):
                                one_ip["host"], one_ip["port"] = split_maohao(one_ip.get("ip"))
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
                
            print(ALLHOST)
            if item.name.endswith("txt"):
                """to do"""

reload_ip()
            
 