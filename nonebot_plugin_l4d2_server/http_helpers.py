"""HTTP helpers: file download, byte fetching, common headers."""

from __future__ import annotations

from pathlib import Path

import aiofiles
import aiohttp
from aiohttp import ClientTimeout
from nonebot.log import logger

DEFAULT_TIMEOUT = ClientTimeout(total=600)

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) "
        "Gecko/20100101 Firefox/107.0"
    ),
}


async def url_to_byte(url: str) -> bytes | None:
    """Download ``url`` to bytes. Returns ``None`` on non-200 or error."""
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
            headers=DEFAULT_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            if resp.status == 200:
                return await resp.read()
            return None


async def save_url_to_file(url: str, dest: Path) -> str | None:
    """Download ``url`` to ``dest``. Returns status message or ``None`` on failure."""
    try:
        data = await url_to_byte(url)
        if not data:
            return None
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
    except Exception as exc:
        logger.info(f"文件获取失败: {exc}")
    else:
        return "下载完成"
        return None


def list_vpk(map_path: Path) -> list[str]:
    """Return all .vpk filenames under ``map_path``."""
    return [p.name for p in map_path.glob("*.vpk")]


def split_maohao(msg: str) -> tuple[str, int]:
    """Parse ``host:port`` string. Defaults to port 20715 if no port given."""
    if ":" in msg:
        return msg.split(":")[0], int(msg.split(":")[-1])
    if "：" in msg:
        return msg.split("：")[0], int(msg.split("：")[-1])
    if msg.replace(".", "").isdigit():
        return msg, 20715
    return "", -1
