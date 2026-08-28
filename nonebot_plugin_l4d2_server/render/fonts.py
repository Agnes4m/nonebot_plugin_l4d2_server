"""Font loading with caching."""

from __future__ import annotations

from functools import lru_cache

from PIL import ImageFont

from nonebot_plugin_l4d2_server.consts import FONT_PATH


@lru_cache(maxsize=8)
def core_font(size: int) -> ImageFont.FreeTypeFont:
    """Cached PIL font at the given size."""
    return ImageFont.truetype(str(FONT_PATH), size=size)
