from pathlib import Path
from typing import Dict, List, Optional, cast

from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage

from ..config import server_all_path
from ..utils.api.models import AllServer, NserverOut
from ..utils.utils import split_maohao
from .draw_msg import draw_one_ip, get_much_server
from .tj import tj_request as tj_request
from .typing import ALLHOST, COMMAND
from .utils import (
    _calculate_server_stats,
    _format_server_summary,
    _get_server_json,
    _handle_group_info,
    _handle_single_server_with_endpoint,
    get_server_endpoint,
)

try:
    import ujson as json
except ImportError:
    import json


async def get_all_server_detail() -> str:
    """获取所有服务器的详细信息"""
    out_list: List[AllServer] = []
    for group in ALLHOST:
        msg_list = await get_group_detail(group)
        if not msg_list:
            continue

        active_server, max_server, active_player, max_player = _calculate_server_stats(
            msg_list,
        )

        data = {
            "command": group,
            "active_server": active_server,
            "max_server": max_server,
            "active_player": active_player,
            "max_player": max_player,
        }
        out_list.append(cast(AllServer, data))

    return _format_server_summary(out_list)


async def get_server_detail(
    command: str = "",
    _id: Optional[str] = None,
    is_img: bool = True,
):
    """异步获取服务器详细信息"""
    server_json = _get_server_json(command, ALLHOST)
    logger.debug(server_json)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    # 输出组服务器信息
    if _id is None:
        return await _handle_group_info(server_json, command, is_img)

    endpoint = await get_server_endpoint(server_json, _id)
    if endpoint is None:
        logger.warning("未找到这个服务器")
        return None

    host, port = endpoint
    out_msg = await _handle_single_server_with_endpoint(is_img, host, port)
    if isinstance(out_msg, bytes):
        return UniMessage.image(raw=out_msg) + UniMessage.text(
            f"connect {endpoint[0]}:{endpoint[1]}",
        )
    if isinstance(out_msg, str):
        return UniMessage.text(out_msg)
    return None


async def get_group_detail(
    command: str,
):
    """根据组获取所有返回服务器信息"""
    server_json = _get_server_json(command, ALLHOST)
    # logger.debug(f"获取组服务器信息: {server_json}")
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    logger.info("正在请求组服务器信息")
    return await get_much_server(server_json, command)


async def get_ip_server(ip: str):
    host, port = split_maohao(ip)
    return await draw_one_ip(host, port)


# 以下是重载ip
def reload_ip():
    global COMMAND

    group_ip = []
    for item in server_all_path.iterdir():
        if item.is_file() and item.name.endswith("json"):
            json_data = json.loads(item.read_text(encoding="utf-8"))
            group_server = cast(Dict[str, List[NserverOut]], json_data)

            for group, group_ip in group_server.items():
                # 处理整个服务器组
                def _process_server_group(server_group: List[dict]) -> None:
                    """
                    处理服务器组中每个配置项的字段逻辑

                    参数:
                        server_group: 服务器组配置列表，每个元素为服务器配置字典
                    输出:
                        无，直接修改传入的列表元素
                    """
                    for one_ip in server_group:
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

                # 处理组更新逻辑
                def _update_global_state(
                    group_name: str,
                    servers: List[dict],
                    item: Path,
                ) -> None:
                    """
                    更新全局状态并记录日志

                    参数:
                        group_name: 服务器组名称
                        servers: 处理后的服务器配置列表
                    输出:
                        无，直接修改全局变量ALLHOST和COMMAND
                    """
                    global ALLHOST
                    ALLHOST.update({group_name: servers})
                    COMMAND.add(group_name)
                    logger.success(
                        f"成功加载 {item.name.split('.')[0]} {len(servers)}个",
                    )

                # 执行处理流程
                _process_server_group(group_ip)
                _update_global_state(group, group_ip, item)


async def server_find(
    command: str = "",
    _id: Optional[str] = None,
    is_img: bool = True,
):
    all_command = get_all_json_filenames()
    server_json = []
    for one_command in all_command:
        server_j = _get_server_json(one_command, ALLHOST)
        if server_j is not None:
            server_json.extend(server_j)
    if server_json is None:
        logger.warning("未找到这个组")
        return None

    # 输出组服务器信息
    if _id is None:
        return await _handle_group_info(server_json, command, is_img)

    endpoint = await get_server_endpoint(server_json, _id)
    if endpoint is None:
        logger.warning("未找到这个服务器")
        return None

    host, port = endpoint
    out_msg = await _handle_single_server_with_endpoint(is_img, host, port)
    if isinstance(out_msg, bytes):
        return UniMessage.image(raw=out_msg) + UniMessage.text(
            f"connect {endpoint[0]}:{endpoint[1]}",
        )
    if isinstance(out_msg, str):
        return UniMessage.text(out_msg)
    return None


def get_all_json_filenames():
    """
    获取 server_all_path 路径下所有 json 文件的文件名（不带扩展名）的列表。
    """
    json_files = []
    for item in server_all_path.iterdir():
        if item.is_file() and item.suffix == ".json":
            json_files.append(item.stem)
    return json_files
