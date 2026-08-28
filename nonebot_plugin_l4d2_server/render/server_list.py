"""Server-list HTML rendering via nonebot_plugin_htmlrender.

Replaces ``presentation/render/html_img.py``.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from a2s.players import Player
from jinja2 import Environment, FileSystemLoader
from nonebot.log import logger
from nonebot_plugin_htmlrender import html_to_pic

from config import config  # injected at runtime
from consts import RENDER_TEMPLATES_PATH, RENDER_BACKGROUNDS_PATH
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


async def _build_html(server_dict: list[dict]) -> str:
    env = _get_env()
    template_name = "normal.html" if config.l4_style == "default" else "normal_old.html"
    template = env.get_template(template_name)

    bg_dir = RENDER_BACKGROUNDS_PATH
    bg_files = [
        f.name for f in bg_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]
    bg_filename = f"back_img/{bg_files[0]}" if bg_files else "background.jpg"

    return await template.render_async(
        servers=server_dict,
        max_count=config.l4_players,
        bg_filename=bg_filename,
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
            max_duration = (
                max(
                    len(str(await convert_duration(p.duration)))
                    for p in sorted_players
                )
                if sorted_players
                else 1
            )
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