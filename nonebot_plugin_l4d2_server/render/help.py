"""Help-card image rendering. + ``core/help/__init__.py``. Reads
``render/help/Help.json`` and produces a help image with section grid.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, cast

import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..consts import (
    HELP_DATA_PATH,
    HELP_ICONS_PATH,
    HELP_TEXTURES_PATH,
)
from ..version import __version__
from .fonts import core_font
from .images import convert_img

ICON_DIR = HELP_ICONS_PATH
DEFAULT_ICON = ICON_DIR / "拼图.png"


def _load_icon(name: str, icon_dir: Path) -> Optional[Image.Image]:
    path = icon_dir / f"{name}.png"
    if path.exists():
        return Image.open(path)
    for icon in icon_dir.glob("*.png"):
        if icon.stem in name:
            return Image.open(icon)
            break
    return None


def get_icon(name: str) -> Image.Image:
    icon = _load_icon(name, ICON_DIR)
    if icon is None:
        icon = Image.open(DEFAULT_ICON)
    return icon.resize((36, 36))


async def render_help(
    name: str,
    sub_text: str,
    help_data: Dict[str, dict],
    bg: Image.Image,
    icon_img: Image.Image,
    badge: Image.Image,
    banner: Image.Image,
    button: Image.Image,
    font: Callable[[int], ImageFont.FreeTypeFont],
    text_color: Tuple[int, int, int] = (23, 67, 91),
    sub_color: Optional[Tuple[int, int, int]] = None,
    title_color: Tuple[int, int, int] = (23, 67, 91),
    sub_title_color: Tuple[int, int, int] = (49, 110, 144),
    sv_color: Tuple[int, int, int] = (23, 67, 91),
    sv_desc_color: Tuple[int, int, int] = (49, 110, 144),
    column: int = 4,
    is_gaussian: bool = False,
    gaussian_blur: int = 20,
) -> bytes:
    if sub_color is None:
        sub_color = cast(
            Tuple[int, int, int],
            tuple(x + 50 if x < 205 else x for x in text_color),
        )

    base_h = 600
    w, h = 50 + 260 * column, base_h + 30
    button_x = 260
    button_y = 103

    title = Image.new("RGBA", (w, base_h))
    icon_img = icon_img.resize((300, 300))
    title.paste(icon_img, (int((w - 300) / 2), 89), icon_img)
    title.paste(badge, (int((w - 900) / 2), 390), badge)
    badge_s = badge.resize((720, 80))
    title.paste(badge_s, (int((w - 720) / 2), 480), badge_s)

    title_draw = ImageDraw.Draw(title)
    title_draw.text((int(w / 2), 440), f"{name} 帮助", title_color, font(36), "mm")
    title_draw.text(
        (int(w / 2), 520),
        sub_text,
        sub_title_color,
        font(26),
        "mm",
    )

    sv_img_list: List[Image.Image] = []
    for sv_name, info in help_data.items():
        tr_size = len(info["data"])
        y_offset = 100 + ((tr_size + column - 1) // column) * button_y
        h += y_offset

        sv_img = Image.new("RGBA", (w, y_offset))
        sv_data = info["data"]
        sv_desc = info["desc"]

        bc = deepcopy(banner)
        bc_draw = ImageDraw.Draw(bc)
        bc_draw.text((30, 25), sv_name, sv_color, font(35), "lm")

        bbox = font(35).getbbox(sv_name)
        size = bbox[2] - bbox[0]
        bc_draw.text((42 + size, 30), sv_desc, sv_desc_color, font(20), "lm")
        sv_img.paste(bc, (0, 10), bc)

        for index, tr in enumerate(sv_data):
            bt = deepcopy(button)
            bt_draw = ImageDraw.Draw(bt)
            tr_name = tr["name"]
            f = 38
            bt.paste(get_icon(tr_name), (14, 20), get_icon(tr_name))
            bt_draw.text((20 + f, 28), tr_name, text_color, font(26), "lm")
            bt_draw.text((20 + f, 50), tr["eg"], sub_color, font(17), "lm")
            bt_draw.text((20, 78), tr["desc"], text_color, font(16), "lm")

            offset_x = button_x * (index % column)
            offset_y = button_y * (index // column)
            sv_img.paste(bt, (25 + offset_x, 83 + offset_y), bt)

        sv_img_list.append(sv_img)

    img = _crop_center(bg, w, h)
    if is_gaussian:
        img = img.filter(ImageFilter.GaussianBlur(gaussian_blur))
    img.paste(title, (0, 0), title)
    temp = 0
    for sm in sv_img_list:
        img.paste(sm, (0, base_h + temp), sm)
        temp += sm.size[1]

    img = img.convert("RGBA")
    bg_white = Image.new("RGBA", img.size, (255, 255, 255))
    img = Image.alpha_composite(bg_white, img).convert("RGB")

    help_path = Path("data/L4D2/help") / f"{name}.jpg"
    help_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(help_path, "JPEG", quality=95, subsampling=0)
    return await convert_img(img)


def _crop_center(img: Image.Image, w: int, h: int) -> Image.Image:
    """Crop to (w, h) preserving aspect ratio."""
    import math

    based_scale = "%.3f" % (w / h)
    img_w, img_h = img.size
    scale_f = "%.3f" % (img_w / img_h)
    new_w = math.ceil(h * float(scale_f))
    new_h = math.ceil(w / float(scale_f))
    if scale_f > based_scale:
        resized = img.resize((new_w, h), Image.Resampling.LANCZOS)
        x1 = int(new_w / 2 - w / 2)
        return resized.crop((x1, 0, x1 + w, h))
    resized = img.resize((w, new_h), Image.Resampling.LANCZOS)
    y1 = int(new_h / 2 - h / 2)
    return resized.crop((0, y1, w, y1 + h))


async def build_help_image() -> bytes | str:
    """Load Help.json + assets, return the rendered help image bytes."""
    async with aiofiles.open(HELP_DATA_PATH, "r", encoding="utf-8") as f:
        help_data = json.loads(await f.read())

    bg_file = HELP_TEXTURES_PATH / "bg.jpg"
    if bg_file.is_file():
        bg_out = Image.open(bg_file).convert("RGB")
    else:  # 兜底：缺背景资源时生成浅色渐变，保证帮助图可用
        bg_out = Image.new("RGB", (2200, 1500))
        _d = ImageDraw.Draw(bg_out)
        for _y in range(1500):
            _t = _y / 1500
            _c = tuple(
                int(a + (b - a) * _t) for a, b in zip((224, 240, 248), (250, 252, 254))
            )
            _d.line([(0, _y), (2200, _y)], fill=_c)
    bg_new = Image.new(
        "RGBA",
        (bg_out.width, bg_out.height),
        (255, 255, 255, 100),
    )
    bg_out.paste(bg_new, None, bg_new)

    return await render_help(
        "L4插件",
        f"版本号:{__version__}",
        help_data,
        bg_out,
        Image.open(HELP_TEXTURES_PATH / "icon.png"),
        Image.open(HELP_TEXTURES_PATH / "badge.png"),
        Image.open(HELP_TEXTURES_PATH / "banner.png"),
        Image.open(HELP_TEXTURES_PATH / "button.png"),
        core_font,
        is_gaussian=False,
        column=4,
        text_color=(23, 67, 91),
        sub_color=(49, 110, 144),
    )
