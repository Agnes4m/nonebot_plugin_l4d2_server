"""字体加载与缓存。

字体来源优先级：``L4_FONT`` 配置 > 包内 ``loli.ttf`` > 系统字体。路径在第一次
调用时决定并缓存，``L4_FONT`` 改动后需要重启 bot（和配置项文档一致）。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from nonebot.log import logger
from PIL import ImageFont

from ..config import config
from ..consts import FONT_PATH

#: 找不到任何字体时的最后兜底（PIL 内置位图字体，不含汉字）。
_SYSTEM_FALLBACKS = ("msyh.ttc", "simhei.ttf", "DejaVuSans.ttf")


@lru_cache(maxsize=1)
def resolve_font_path() -> Optional[str]:
    """决定实际使用的字体文件路径；全部候选都不可用时返回 ``None``。"""
    custom = (config.l4_font or "").strip()
    if custom:
        path = Path(custom).expanduser()
        if path.is_file():
            logger.info(f"[l4] 使用 L4_FONT 指定的字体: {path}")
            return str(path)
        logger.warning(f"[l4] L4_FONT 指向的文件不存在，回退内置字体: {path}")

    if FONT_PATH.is_file():
        return str(FONT_PATH)

    for name in _SYSTEM_FALLBACKS:
        try:
            ImageFont.truetype(name, 12)
        except OSError:
            continue
        logger.info(f"[l4] 内置字体缺失，使用系统字体: {name}")
        return name

    logger.error("[l4] 找不到任何可用字体，中文会渲染成方块")
    return None


@lru_cache(maxsize=32)
def core_font(size: int) -> ImageFont.FreeTypeFont:
    """Cached PIL font at the given size."""
    path = resolve_font_path()
    if path is None:
        return ImageFont.load_default(size)
    try:
        return ImageFont.truetype(path, size)
    except OSError as exc:
        logger.warning(f"[l4] 加载字体 {path} 失败（{exc}），改用 PIL 内置字体")
        return ImageFont.load_default(size)


def reload_font() -> None:
    """清空字体缓存，下次调用重新解析 ``L4_FONT``。"""
    resolve_font_path.cache_clear()
    core_font.cache_clear()
