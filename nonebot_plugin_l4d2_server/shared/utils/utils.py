import json
from pathlib import Path
from typing import List, Tuple

import aiofiles
import aiohttp
from aiohttp import ClientTimeout
from nonebot.log import logger


def read_config(config_path: Path) -> dict:
    if not config_path.is_file():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def write_config(config_path: Path, data: dict) -> None:
    try:
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        raise RuntimeError(f"配置写入失败: {e}") from e


async def get_file(url: str, down_file: Path):
    try:
        maps = await url_to_byte(url)
        if maps:
            async with aiofiles.open(down_file, "wb") as mfile:
                await mfile.write(maps)
            return "文件已下载，正在解压"
    except Exception as e:
        logger.info(f"文件获取不到/已损坏: {e}")
        return None


def get_vpk(map_path: Path, file_: str = ".vpk") -> List[str]:
    return [str(file) for file in map_path.glob(f"*{file_}")]


def mes_list(mes: str, name_list: List[str]) -> str:
    if name_list:
        for idx, name in enumerate(name_list):
            mes += f"\n{idx + 1}、{name}"
    return mes


def split_maohao(msg: str) -> Tuple[str, int]:
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
    if url.startswith("file://"):
        local_path = Path(url[7:])
        if local_path.is_file():
            async with aiofiles.open(local_path, "rb") as f:
                return await f.read()
        logger.warning(f"本地文件不存在: {local_path}")
        return None

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
            timeout=ClientTimeout(total=600),
        ) as resp:
            if resp.status == 200:
                return await resp.read()
            return None
