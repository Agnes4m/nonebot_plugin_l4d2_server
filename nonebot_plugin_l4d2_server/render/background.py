"""Background image selection from user's custom_backgrounds directory."""

from __future__ import annotations

import random
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
from nonebot.log import logger
from PIL import Image

from ..config import config

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")


def user_background_dir() -> Path:
    """用户自定义背景目录：``config.data_dir / custom_backgrounds``。"""
    return config.data_dir / "custom_backgrounds"


def list_image_files(directory: Path) -> list[Path]:
    """``directory`` 下的所有图片文件（按文件名排序）；目录不存在或不可读返回空列表。"""
    if not directory.is_dir():
        return []
    try:
        return sorted(
            p
            for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES
        )
    except OSError as exc:
        logger.warning(f"读取背景目录 {directory} 失败: {exc}")
        return []


def pick_random_user_background() -> Optional[Path]:
    """从用户背景目录随机抽一张；空则返回 None。"""
    files = list_image_files(user_background_dir())
    return random.choice(files) if files else None


def ensure_user_background_dir() -> Path:
    """确保用户背景目录存在，返回该目录。"""
    directory = user_background_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def pick_background(
    url: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Image.Image:
    """通用背景图选择器（公开 API，供外部插件复用）。"""
    if url:
        # httpx 0.28+ 同步 ``get`` 已 deprecated；走 ``Client.get`` 保持向后兼容。
        with httpx.Client() as client:
            resp = client.get(url, timeout=10.0)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content)).convert("RGBA")

    files = list_image_files(user_background_dir())
    if files:
        chosen = random.choice(files)
        try:
            return Image.open(chosen).convert("RGBA")
        except Exception as exc:
            logger.warning(f"打开自定义背景失败: {chosen.name}: {exc}")

    if width and height:
        return Image.new("RGBA", (width, height), (255, 255, 255, 255))
    return Image.new("RGBA", (1, 1), (255, 255, 255, 255))
