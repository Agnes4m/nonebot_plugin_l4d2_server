import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import aiohttp
import nonebot
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage


async def get_file(url: str, down_file: Path):
    """
    下载指定Url到指定位置
    """
    try:
        maps = await url_to_byte(url)
        logger.info("已获取文件，尝试新建文件并写入")
        if maps:
            async with aiofiles.open(down_file, "wb") as mfile:
                await mfile.write(maps)
            logger.info("下载成功")
            return "文件已下载，正在解压"
    except Exception as e:
        logger.info(f"文件获取不到/已损坏:原因是{e}")
        return None


def get_vpk(map_path: Path, file_: str = ".vpk") -> List[str]:
    """
    获取路径下所有vpk文件名，并存入vpk_list列表中
    """
    vpk_list: List[str] = [str(file) for file in map_path.glob(f"*{file_}")]
    return vpk_list


def mes_list(mes: str, name_list: List[str]) -> str:
    if name_list:
        for idx, name in enumerate(name_list):
            mes += f"\n{idx + 1}、{name}"
    return mes


def del_map(num: int, map_path: Path) -> str:
    """
    删除指定的地图
    """
    map_ = get_vpk(map_path)
    map_name = map_[num - 1]
    del_file = map_path / map_name
    del_file.unlink()
    return map_name


def rename_map(num: int, rename: str, map_path: Path) -> str:
    """
    改名指定的地图
    """
    map_ = get_vpk(map_path)
    map_name = map_[num - 1]
    old_file = map_path / map_name
    new_file = map_path / rename
    old_file.rename(new_file)
    logger.info("改名成功")
    return map_name


def solve(msg: str):
    """删除str最后一行"""
    lines = msg.splitlines()
    lines.pop()
    return "\n".join(lines)


def at_to_usrid(at: List[int]):
    return at[0] if at else None


async def save_file(file: bytes, path_name: str):
    """保存文件"""
    async with aiofiles.open(path_name, "wb") as files:
        await files.write(file)


async def upload_file(bot: Bot, event: MessageEvent, file_data: bytes, filename: str):
    """上传临时文件"""
    if os.name == "nt":
        with tempfile.TemporaryDirectory() as temp_dir:
            async with aiofiles.open(Path(temp_dir) / filename, "wb") as f:
                await f.write(file_data)
            if isinstance(event, GroupMessageEvent):
                await bot.call_api(
                    "upload_group_file",
                    group_id=event.group_id,
                    file=f.name,
                    name=filename,
                )
            else:
                await bot.call_api(
                    "upload_private_file",
                    user_id=event.user_id,
                    file=f.name,
                    name=filename,
                )
        (Path().joinpath(filename)).unlink()
    else:
        with tempfile.NamedTemporaryFile("wb+") as f:
            f.write(file_data)
        if isinstance(event, GroupMessageEvent):
            await bot.call_api(
                "upload_group_file",
                group_id=event.group_id,
                file=f.name,
                name=filename,
            )
        else:
            await bot.call_api(
                "upload_private_file",
                user_id=event.user_id,
                file=f.name,
                name=filename,
            )


sub_menus = []


def register_menu_func(
    func: str,
    trigger_condition: str,
    brief_des: str,
    trigger_method: str = "指令",
    detail_des: Optional[str] = None,
):
    sub_menus.append(
        {
            "func": func,
            "trigger_method": trigger_method,
            "trigger_condition": trigger_condition,
            "brief_des": brief_des,
            "detail_des": detail_des or brief_des,
        },
    )


def register_menu(*args, **kwargs):
    def decorator(f):  # noqa: ANN001
        register_menu_func(*args, **kwargs)
        return f

    return decorator


async def extract_last_digit(msg: str) -> Tuple[str, str]:
    "分离str和数字"
    for i in range(len(msg) - 1, -1, -1):
        if msg[i].isdigit():
            last_digit = msg[i]
            new_msg = msg[:i]
            return new_msg, last_digit
    return msg, ""


def split_maohao(msg: str) -> Tuple[str, int]:
    """分割大小写冒号"""
    if ":" in msg:
        return msg.split(":")[0], int(msg.split(":")[-1])
    if "：" in msg:
        return msg.split("：")[0], int(msg.split("：")[-1])
    if msg.replace(".", "").isdigit():
        return msg, 20715
    return "", -1


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
}


async def url_to_byte(url: str):
    """获取URL数据的字节流"""

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=600) as response:
            if response.status == 200:
                return await response.read()
            return None


async def url_to_msg(url: str):
    """获取URL数据的字节流"""

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=600) as response:
            if response.status == 200:
                return await response.text()
            return None


async def get_message_at(datas: str) -> Optional[int]:
    data: Dict[str, Any] = json.loads(datas)
    at_list = [int(msg["data"]["qq"]) for msg in data["message"] if msg["type"] == "at"]
    return at_list[0] if at_list else None


async def send_ip_msg(msg: str):
    try:
        await UniMessage.text(msg).finish()
    except nonebot.adapters.qq:
        msg_new = msg.split("\n")[:-2]
        msg_out = "\n".join(msg_new)
        await UniMessage.text(msg_out).send()
