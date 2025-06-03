from pathlib import Path
from typing import Dict, Union

import aiofiles
from msgspec import json as msgjson
from PIL import Image

from ..config import ICONPATH
from ..l4_image.convert import core_font
from ..l4_image.model import PluginHelp
from .draw import get_help

__version__ = "1.0.2"
TEXT_PATH = Path(__file__).parent / "texture2d"
HELP_DATA = Path(__file__).parent / "Help.json"


async def get_help_data() -> Union[Dict[str, PluginHelp], None]:
    if HELP_DATA.exists():
        async with aiofiles.open(HELP_DATA, "rb") as file:
            return msgjson.decode(
                await file.read(),
                type=Dict[str, PluginHelp],
            )
    return None


async def get_l4d2_core_help() -> Union[bytes, str]:
    help_data = await get_help_data()
    if help_data is None:
        return "暂未找到帮助数据..."

    bg_out = Image.open(TEXT_PATH / "bg.jpg")
    bg_new = Image.new(
        "RGBA",
        (bg_out.width, bg_out.height),
        (255, 255, 255, 100),
    )
    bg_out.paste(bg_new, None, bg_new)

    return await get_help(
        "L4插件",
        f"版本号:{__version__}",
        help_data,
        bg_out,
        Image.open(TEXT_PATH / "icon.png"),
        Image.open(TEXT_PATH / "badge.png"),
        Image.open(TEXT_PATH / "banner.png"),
        Image.open(TEXT_PATH / "button.png"),
        core_font,
        is_dark=False,
        column=4,
        is_gaussian=False,
        text_color=(23, 67, 91),
        sub_c=(49, 110, 144),
        icon_path=ICONPATH,
    )
