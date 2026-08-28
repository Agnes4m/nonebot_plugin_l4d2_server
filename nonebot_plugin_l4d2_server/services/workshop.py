"""Steam Workshop download flow. (the render function moved to
``render/workshop.py``; this module orchestrates the full
lookup → confirm → download → write flow).
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import aiofiles
from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage

from ..api import WorksopInfo
from ..config import config
from ..http_helpers import url_to_byte
from ..render.workshop import render_workshop_card
from ..services.local_server import addons_dir


def parse_workshop_id(input_str: str) -> str:
    """Accept either a numeric id or a full steamcommunity.com URL."""
    if input_str.isdigit():
        return input_str
    if input_str.startswith("https://steamcommunity.com/sharedfiles/filedetails"):
        params = parse_qs(urlparse(input_str).query)
        if "id" in params and params["id"][0].isdigit():
            return params["id"][0]
    raise ValueError("无效的steam链接，请输入工坊ID或完整URL")


async def fetch_info(workshop_input: str) -> WorksopInfo:
    """Resolve input → render card → return raw info dict."""
    workshop_id = parse_workshop_id(workshop_input)
    return await render_workshop_card(workshop_id)


async def download_to_addons(info: WorksopInfo, server_index: int) -> Path | None:
    """Download the workshop file into the chosen server's ``addons`` folder.

    Returns the saved path, or ``None`` if the file already exists or the
    download fails.
    """
    addons = addons_dir(server_index) or (Path(config.l4_path) / "addons")
    addons.mkdir(parents=True, exist_ok=True)

    target = addons / info["filename"]
    if target.is_file():
        logger.info(f"地图文件已存在: {target}")
        await UniMessage.text(f"地图已存在: {info['filename']}").finish()
        return None

    data = await url_to_byte(info["file_url"])
    if data is None:
        logger.error(f"下载失败: {info['file_url']}")
        await UniMessage.text("下载失败").finish()
        return None

    async with aiofiles.open(target, "wb") as f:
        await f.write(data)

    logger.info(f"地图下载完成: {target}")
    await UniMessage.text(f"✅ 地图下载完成: {info['filename']}").send()
    await UniMessage.file(path=target, name=f"{info['title']}.vpk").send()
    return target
