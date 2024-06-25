import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import httpx
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.log import logger
from nonebot.matcher import Matcher

from .config import l4_config, systems
from .steam import url_to_byte

# from .rule import
from .txt_to_img import mode_txt_to_img


async def get_file(url: str, down_file: Path):
    """
    下载指定Url到指定位置
    """
    try:
        if l4_config.l4_only:
            maps = await url_to_byte(url)
        else:
            maps = httpx.get(url).content  # noqa: ASYNC100
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
            mes += f"\n{idx+1}、{name}"
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


async def get_message_at(datas: str) -> List[int]:
    data: Dict[str, Any] = json.loads(datas)
    return [int(msg["data"]["qq"]) for msg in data["message"] if msg["type"] == "at"]


def at_to_usrid(at: List[int]):
    return at[0] if at else None


async def save_file(file: bytes, path_name):
    """保存文件"""
    async with aiofiles.open(path_name, "wb") as files:
        await files.write(file)


async def upload_file(bot: Bot, event: MessageEvent, file_data: bytes, filename: str):
    """上传临时文件"""
    if systems in ["win", "other"]:
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
    elif systems == "linux":
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
    def decorator(f):
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


async def str_to_picstr(push_msg: str, matcher: Matcher, keyword: Optional[str] = None):
    """判断图片输出还是正常输出"""
    if l4_config.l4_image:
        lines = push_msg.splitlines()
        first_str = lines[0]
        last_str = lines[-1]
        push_msg = "\n".join(lines[1:-1])
        if l4_config.l4_connect:
            await mode_txt_to_img(first_str, push_msg, last_str)
        else:
            await mode_txt_to_img(first_str, push_msg)
    else:
        if l4_config.l4_connect or keyword == "connect":
            await matcher.send(push_msg)
        else:
            await matcher.send("\n".join(push_msg.splitlines()[1:-2]))


def split_maohao(msg: str) -> List[str]:
    """分割大小写冒号"""
    if ":" in msg:
        msgs: List[str] = msg.split(":")
    elif "：" in msg:
        msgs: List[str] = msg.split("：")
    elif msg.replace(".", "").isdigit():
        msgs: List[str] = [msg, "20715"]
    else:
        msgs = []
    return [msgs[0], msgs[-1]]
