"""PIL image primitives: cropping, text layout, format conversion."""

from __future__ import annotations

import math
from base64 import b64encode
from io import BytesIO

import aiofiles
from PIL import Image, ImageDraw
from nonebot.log import logger

from consts import JPEG_QUALITY
from .fonts import core_font


def crop_center_img(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize-then-center-crop ``img`` to the given dimensions."""
    based_scale = "%.3f" % (target_w / target_h)
    w, h = img.size
    scale_f = "%.3f" % (w / h)
    new_w = math.ceil(target_h * float(scale_f))
    new_h = math.ceil(target_w / float(scale_f))
    if scale_f > based_scale:
        resized = img.resize((new_w, target_h), Image.Resampling.LANCZOS)
        x1 = int(new_w / 2 - target_w / 2)
        x2 = int(new_w / 2 + target_w / 2)
        return resized.crop((x1, 0, x2, target_h))
    resized = img.resize((target_w, new_h), Image.Resampling.LANCZOS)
    y1 = int(new_h / 2 - target_h / 2)
    y2 = int(new_h / 2 + target_h / 2)
    return resized.crop((0, y1, target_w, y2))


def draw_center_text_by_line(
    img_draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font,
    fill,
    max_length: float,
    not_center: bool = False,
) -> float:
    """Word-wrap ``text`` into ``img_draw`` starting at ``pos``."""
    pun = "。！？；!?…"
    gun = "。！？；!?」』"
    x, y = pos
    bbox = font.getbbox("X")
    _, h = bbox[3] - bbox[1], 0
    line = ""
    length = 0
    anchor = "la" if not_center else "mm"
    for index, char in enumerate(text):
        bbox = font.getbbox(char)
        size = bbox[2] - bbox[0]
        length += size
        line += char
        if length < max_length and char not in pun and char != "\n":
            continue
        if index + 1 < len(text) and text[index + 1] in gun:
            continue
        line = line.replace("\n", "")
        img_draw.text((x, y), line, fill, font, anchor)
        line, length = "", 0
        y += h * 1.5
    else:
        img_draw.text((x, y), line, fill, font, anchor)
    return y


async def convert_img(img: Image.Image) -> bytes:
    """Encode ``img`` to JPEG bytes."""
    logger.info("处理图片中...")
    img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


async def text2pic(text: str, max_size: int = 800, font_size: int = 24) -> bytes:
    """Render plain text as a PNG-like JPEG card (white background)."""
    if text.endswith("\n"):
        text = text[:-1]

    line_count = text.count("\n") + 1
    line_height = int(font_size * 1.2)
    estimated_height = line_count * line_height + 80

    img = Image.new("RGB", (max_size, estimated_height), (255, 255, 255))
    draw = ImageDraw.ImageDraw(img)
    y = draw_center_text_by_line(
        draw,
        (50, 30),
        text,
        core_font(font_size),
        "black",
        max_size - 80,
        not_center=True,
    )
    img = img.crop((0, 0, max_size, int(y + 55)))
    return await convert_img(img)


async def to_base64(img_or_path) -> str:
    """Convert PIL image or path to ``base64://...`` string."""
    from pathlib import Path

    if isinstance(img_or_path, bytes):
        return f"base64://{b64encode(img_or_path).decode()}"

    if isinstance(img_or_path, Image.Image):
        return f"base64://{b64encode(await convert_img(img_or_path)).decode()}"

    async with aiofiles.open(Path(img_or_path), "rb") as f:
        return f"base64://{b64encode(await f.read()).decode()}"


async def convert_duration(duration: float) -> str:
    """Convert seconds to ``Hh Mm Ss`` form."""
    total = int(duration)
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    out = ""
    if hours:
        out += f"{hours}h "
    if minutes:
        out += f"{minutes}m "
    out += f"{seconds}s"
    return out