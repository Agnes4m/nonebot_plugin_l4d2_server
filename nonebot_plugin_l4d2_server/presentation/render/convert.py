from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Union, overload

import aiofiles
from nonebot.log import logger

from .image_tools import draw_center_text_by_line

FONT_PATH = Path(__file__).parent.parent.parent / "domain/font/loli.ttf"
pic_quality: int = 95


@lru_cache(maxsize=8)
def core_font(size: int):
    from PIL import ImageFont

    return ImageFont.truetype(str(FONT_PATH), size=size)


@overload
async def convert_img(
    img: Image.Image,
    is_base64: bool = False,
) -> bytes: ...


@overload
async def convert_img(
    img: Image.Image,
    is_base64: bool = True,  # noqa: FBT001
) -> str: ...


@overload
async def convert_img(
    img: bytes,
    is_base64: bool = False,
) -> str: ...


@overload
async def convert_img(
    img: Path,
    is_base64: bool = False,
) -> str: ...


async def convert_img(
    img: Union[Image.Image, str, Path, bytes],
    is_base64: bool = False,
):
    """
    :说明:
      将PIL.Image对象转换为bytes或者base64格式。
    :参数:
      * img (Image): 图片。
      * is_base64 (bool): 是否转换为base64格式, 不填默认转为bytes。
    :返回:
      * res: bytes对象或base64编码图片。
    """
    from PIL import Image

    logger.info("处理图片中....")

    if isinstance(img, Image.Image):
        img = img.convert("RGB")
        result_buffer = BytesIO()
        img.save(result_buffer, format="JPEG", quality=95)
        res = result_buffer.getvalue()
        if is_base64:
            res = "base64://" + b64encode(res).decode()
        return res
    if isinstance(img, bytes):
        pass
    else:
        async with aiofiles.open(img, "rb") as fp:
            img = await fp.read()

    logger.success("图片处理完成!")

    return f"base64://{b64encode(img).decode()}"


async def text2pic(text: str, max_size: int = 800, font_size: int = 24):
    from PIL import Image, ImageDraw

    if text.endswith("\n"):
        text = text[:-1]

    # 更准确的高度计算
    line_count = text.count("\n") + 1
    line_height = int(font_size * 1.2)  # 每行高度，包含行间距
    estimated_height = line_count * line_height + 80  # 加上上下边距

    img = Image.new(
        "RGB",
        (max_size, estimated_height),
        (255, 255, 255),
    )
    img_draw = ImageDraw.ImageDraw(img)
    y = draw_center_text_by_line(
        img_draw,
        (50, 30),
        text,
        core_font(font_size),
        "black",
        max_size - 80,
        True,  # noqa: FBT003
    )
    # 裁剪时留一些余量
    img = img.crop((0, 0, max_size, int(y + 55)))
    return await convert_img(img)
