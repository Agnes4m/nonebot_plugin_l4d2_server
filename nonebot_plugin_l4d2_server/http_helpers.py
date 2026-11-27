"""HTTP helpers: file download, byte fetching, common headers."""

from __future__ import annotations

from pathlib import Path

import aiofiles
import aiohttp
from aiohttp import ClientTimeout
from nonebot.log import logger

DEFAULT_TIMEOUT = ClientTimeout(total=600)

# 流式下载默认参数：创意工坊单文件常见 100MB~2GB，长 body 但短连接/写盘快。
STREAM_CHUNK_SIZE = 1 << 20  # 1 MiB
STREAM_TIMEOUT = ClientTimeout(total=3600, connect=30, sock_read=60)

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) "
        "Gecko/20100101 Firefox/107.0"
    ),
}


async def url_to_byte(url: str) -> bytes | None:
    """Download ``url`` to bytes. Returns ``None`` on non-200 or error.

    小文件走这条；大文件请用 ``stream_download`` 避免内存峰值。
    """
    if url.startswith("file://"):
        local_path = Path(url[7:])
        if local_path.is_file():  # noqa: ASYNC240
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


async def stream_download(
    url: str,
    dest: Path,
    *,
    chunk_size: int = STREAM_CHUNK_SIZE,
    timeout: ClientTimeout = STREAM_TIMEOUT,
) -> None:
    """流式下载 ``url`` 到 ``dest``。失败抛 ``aiohttp`` / ``OSError``。

    默认 ``chunk_size=1MiB``，``timeout`` 拆 connect/sock_read 避免单次长传被一刀切。
    父目录会自动 ``mkdir -p``。
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=DEFAULT_HEADERS) as resp:
            resp.raise_for_status()
            async with aiofiles.open(dest, "wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    if chunk:
                        await f.write(chunk)


async def save_url_to_file(url: str, dest: Path) -> str | None:
    """Download ``url`` to ``dest``. Returns status message or ``None`` on failure.

    实现已修复：旧版在 ``else`` 分支里 ``return "下载完成"`` 之后还有一个永远
    不可达的 ``return None``；现在直接单 return 路径。
    """
    try:
        data = await url_to_byte(url)
        if not data:
            return None
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
    except Exception as exc:
        logger.info(f"文件获取失败: {exc}")
        return None
    return "下载完成"


def list_vpk(map_path: Path) -> list[str]:
    """Return all .vpk filenames under ``map_path``."""
    return [p.name for p in map_path.glob("*.vpk")]


def split_maohao(msg: str) -> tuple[str, int]:
    """Parse ``host:port`` string. Defaults to port 20715 if no port given.

    非法输入一律返回 ``("", -1)``，**不抛异常**：这个函数被指令参数、SourceBans
    网页解析、registry 归一化等十几处调用，任何一处丢脏数据都不该让整次刷新
    或整条指令崩掉。端口还必须是 1-65535，否则同样按非法处理。
    """
    msg = msg.strip()
    for sep in (":", "："):
        if sep in msg:
            host, _, raw_port = msg.rpartition(sep)
            try:
                port = int(raw_port)
            except ValueError:
                return "", -1
            if not 0 < port <= 65535:
                return "", -1
            return host, port
    if msg.replace(".", "").isdigit():
        return msg, 20715
    return "", -1
