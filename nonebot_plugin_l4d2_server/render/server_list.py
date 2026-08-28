"""Server-list HTML rendering via nonebot_plugin_htmlrender."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from a2s.players import Player
from jinja2 import Environment, FileSystemLoader
from nonebot.log import logger
from nonebot_plugin_htmlrender import html_to_pic

from nonebot_plugin_l4d2_server.config import config
from nonebot_plugin_l4d2_server.consts import (
    CUSTOM_BACKGROUNDS_PATH,
    RENDER_BACKGROUNDS_PATH,
    RENDER_TEMPLATES_PATH,
)

from .images import convert_duration

_template_env: Environment | None = None


def _get_env() -> Environment:
    global _template_env
    if _template_env is None:
        _template_env = Environment(
            loader=FileSystemLoader(str(RENDER_TEMPLATES_PATH)),
            enable_async=True,
            autoescape=True,
        )
    return _template_env


def _resolve_background() -> Path:
    """优先使用用户自定义背景（data/L4D2/custom_backgrounds/），否则用内置默认图。"""
    if CUSTOM_BACKGROUNDS_PATH.is_dir():
        for f in sorted(CUSTOM_BACKGROUNDS_PATH.iterdir()):
            if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                return f
    return RENDER_BACKGROUNDS_PATH / "background.jpg"


def _prepare_back_img() -> str:
    """把选中的背景复制到模板可达的 render/back_img/ 下，返回相对模板的文件名。"""
    src = _resolve_background()
    if not src.is_file():
        return ""
    back_dir = RENDER_TEMPLATES_PATH.parent / "back_img"
    back_dir.mkdir(parents=True, exist_ok=True)
    dst = back_dir / f"bg{src.suffix.lower()}"
    if not dst.is_file() or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)
    return f"back_img/{dst.name}"


async def _build_html(server_dict: list[dict]) -> str:
    env = _get_env()
    template_name = "normal.html" if config.l4_style == "default" else "normal_old.html"
    template = env.get_template(template_name)

    return await template.render_async(
        servers=server_dict,
        max_count=config.l4_players,
        bg_filename=_prepare_back_img(),
    )


async def render_server_list(server_dict: list[dict]) -> Optional[bytes]:
    """Render the list of servers as an HTML image (bytes)."""
    for server_info in server_dict:
        server = server_info["server"]
        server.player_count = server.player_count or 0
        server.max_players = server.max_players or 0
        if server_info.get("player"):
            sorted_players: list[Player] = sorted(
                server_info["player"],
                key=lambda p: p.score,
                reverse=True,
            )[: config.l4_players]
            # async 推导需先物化为列表，max() 不能直接消费 async 生成器
            durations = [
                len(str(await convert_duration(p.duration))) for p in sorted_players
            ]
            max_duration = max(durations) if durations else 1
            for p in sorted_players:
                dur = "{:^{}}".format(await convert_duration(p.duration), max_duration)
                p.name = f"{p.name} | {dur}"
            server_info["player"] = sorted_players
        else:
            server_info["player"] = []

    try:
        content = await _build_html(server_dict)
        return await html_to_pic(
            content,
            wait=0,
            viewport={"width": 100, "height": 100},
            template_path=f"file://{RENDER_TEMPLATES_PATH.absolute()}",
        )
    except Exception as exc:
        logger.warning(f"渲染服务器列表失败: {exc}")
        return None
