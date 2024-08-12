from base64 import b64encode
from io import BytesIO
from pathlib import Path
from typing import Union, overload

import aiofiles
from nonebot.log import logger
from PIL import Image, ImageDraw, ImageFont

from .image_tools import draw_center_text_by_line

FONT_PATH = Path(__file__).parent.parent / "data/font/loli.ttf"
pic_quality: int = 95


def core_font(size: int) -> ImageFont.FreeTypeFont:
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


def convert_img_sync(img_path: Path):
    with img_path.open("rb") as fp:
        img = fp.read()

    return f"base64://{b64encode(img).decode()}"


async def str_lenth(r: str, size: int, limit: int = 540) -> str:  # noqa: RUF029
    result = ""
    temp = 0
    for i in r:
        if i == "\n":
            temp = 0
            result += i
            continue

        if temp >= limit:
            result += "\n" + i
            temp = 0
        else:
            result += i

        if i.isdigit():
            temp += round(size / 10 * 6)
        elif i == "/":
            temp += round(size / 10 * 2.2)
        elif i == ".":
            temp += round(size / 10 * 3)
        elif i == "%":
            temp += round(size / 10 * 9.4)
        else:
            temp += size
    return result


def get_str_size(
    r: str,
    font: ImageFont.FreeTypeFont,
    limit: int = 540,
) -> str:
    result = ""
    line = ""
    for i in r:
        if i == "\n":
            result += f"{line}\n"
            line = ""
            continue

        line += i

        if hasattr(font, "getsize"):
            size, _ = font.getsize(line)  # type: ignore
        else:
            bbox = font.getbbox(line)
            size, _ = bbox[2] - bbox[0], bbox[3] - bbox[1]

        if size >= limit:
            result += f"{line}\n"
            line = ""
    else:
        result += line
    return result


def get_height(content: str, size: int) -> int:
    line_count = content.count("\n")
    return (line_count + 1) * size


async def text2pic(text: str, max_size: int = 800, font_size: int = 24):
    if text.endswith("\n"):
        text = text[:-1]

    img = Image.new(
        "RGB",
        (max_size, len(text) * font_size // 10),
        (255, 255, 255),
    )
    img_draw = ImageDraw.ImageDraw(img)
    y = draw_center_text_by_line(
        img_draw,
        (50, 50),
        text,
        core_font(font_size),
        "black",
        max_size - 80,
        True,  # noqa: FBT003
    )
    img = img.crop((0, 0, max_size, int(y + 80)))
    return await convert_img(img)
