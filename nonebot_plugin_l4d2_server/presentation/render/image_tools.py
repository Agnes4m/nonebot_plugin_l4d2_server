import math
import random
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union

import httpx
from httpx import get
from PIL import Image, ImageDraw, ImageFont

TEXT_PATH = Path(__file__).parent / "texture2d"
BG_PATH = Path(__file__).parents[1] / "default_bg"


async def sget(url: str):
    async with httpx.AsyncClient(timeout=None) as client:  # noqa: S113
        return await client.get(url=url)


def draw_center_text_by_line(
    img: ImageDraw.ImageDraw,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Union[Tuple[int, int, int, int], str],
    max_length: float,
    not_center: bool = False,
) -> float:
    pun = "。！？；!?…"
    gun = "。！？；!?」』"
    x, y = pos

    if hasattr(font, "getsize"):
        _, h = font.getsize("X")  # type: ignore
    else:
        bbox = font.getbbox("X")
        _, h = 0, bbox[3] - bbox[1]

    line = ""
    lenth = 0
    anchor = "la" if not_center else "mm"
    for index, char in enumerate(text):
        if hasattr(font, "getsize"):
            # 获取当前字符的宽度
            size, _ = font.getsize(char)  # type: ignore
        else:
            bbox = font.getbbox(char)
            size, _ = bbox[2] - bbox[0], bbox[3] - bbox[1]
        lenth += size
        line += char
        if lenth < max_length and char not in pun and char != "\n":
            pass
        else:
            if index + 1 < len(text) and text[index + 1] in gun:
                pass
            else:
                line = line.replace("\n", "")
                img.text((x, y), line, fill, font, anchor)
                line, lenth = "", 0
                y += h * 1.5
    else:
        img.text((x, y), line, fill, font, anchor)
    return y


def crop_center_img(
    img: Image.Image,
    based_w: int,
    based_h: int,
) -> Image.Image:
    # 确定图片的长宽
    based_scale = "%.3f" % (based_w / based_h)
    w, h = img.size
    scale_f = "%.3f" % (w / h)
    new_w = math.ceil(based_h * float(scale_f))
    new_h = math.ceil(based_w / float(scale_f))
    if scale_f > based_scale:
        resize_img = img.resize((new_w, based_h), Image.Resampling.LANCZOS)
        x1 = int(new_w / 2 - based_w / 2)
        y1 = 0
        x2 = int(new_w / 2 + based_w / 2)
        y2 = based_h
    else:
        resize_img = img.resize((based_w, new_h), Image.Resampling.LANCZOS)
        x1 = 0
        y1 = int(new_h / 2 - based_h / 2)
        x2 = based_w
        y2 = int(new_h / 2 + based_h / 2)
    return resize_img.crop((x1, y1, x2, y2))


async def get_color_bg(
    based_w: int,
    based_h: int,
    bg_path: Optional[Path] = None,
    without_mask: bool = False,
    is_full: bool = False,
    color: Optional[Tuple[int, int, int]] = None,
    full_opacity: int = 200,
) -> Image.Image:
    ci_img = CustomizeImage(bg_path)  # type: ignore
    img = ci_img.get_image(None, based_w, based_h)
    if color is None:
        color = ci_img.get_bg_color(img)
    if is_full:
        color_img = Image.new("RGBA", (based_w, based_h), color)
        mask = Image.new(
            "RGBA",
            (based_w, based_h),
            (255, 255, 255, full_opacity),
        )
        img.paste(color_img, (0, 0), mask)
    elif not without_mask:
        color_mask = Image.new("RGBA", (based_w, based_h), color)
        enka_mask = Image.open(TEXT_PATH / "bg_mask.png").resize(
            (based_w, based_h),
        )
        img.paste(color_mask, (0, 0), enka_mask)
    return img


class CustomizeImage:
    def __init__(self, bg_path: Path) -> None:
        self.bg_path = bg_path

    def get_image(
        self,
        image: Union[str, Image.Image, None],
        based_w: int,
        based_h: int,
    ) -> Image.Image:
        # 获取背景图片
        if isinstance(image, Image.Image):
            edit_bg = image
        elif image:
            edit_bg = Image.open(BytesIO(get(image).content)).convert("RGBA")
        else:
            _lst = list(self.bg_path.iterdir())
            if _lst:
                path = random.choice(list(self.bg_path.iterdir()))
            else:
                path = random.choice(list(BG_PATH.iterdir()))
            edit_bg = Image.open(path).convert("RGBA")

        # 确定图片的长宽
        return crop_center_img(edit_bg, based_w, based_h)

    @staticmethod
    def get_dominant_color(pil_img: Image.Image) -> Tuple[int, int, int]:
        img = pil_img.copy()
        img = img.convert("RGBA")
        img = img.resize((1, 1), resample=0)
        return img.getpixel((0, 0))  # type: ignore

    @staticmethod
    def get_bg_color(
        edit_bg: Image.Image,
        is_light: Optional[bool] = False,
    ) -> Tuple[int, int, int]:
        # 获取背景主色
        color = 8
        q = edit_bg.quantize(colors=color, method=Image.Quantize.FASTOCTREE)
        bg_color = (0, 0, 0)
        based_light = 195 if is_light else 120
        temp = 9999
        for i in range(color):
            bg = tuple(
                q.getpalette()[  # type:ignore
                    i * 3 : (i * 3) + 3
                ],
            )
            light_value = bg[0] * 0.3 + bg[1] * 0.6 + bg[2] * 0.1
            if abs(light_value - based_light) < temp:
                bg_color = bg
                temp = abs(light_value - based_light)
        return bg_color  # type:ignore

    @staticmethod
    def get_text_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        # 通过背景主色（bg_color）确定文字主色
        r = 125
        if max(*bg_color) > 255 - r:
            r *= -1
        return (
            math.floor(min(bg_color[0] + r, 255)),
            math.floor(min(bg_color[1] + r, 255)),
            math.floor(min(bg_color[2] + r, 255)),
        )

    @staticmethod
    def get_char_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        r = 140
        if max(*bg_color) > 255 - r:
            r *= -1
        return (
            math.floor(bg_color[0] + 5 if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] + 5 if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] + 5 if bg_color[2] + r <= 255 else 255),
        )

    @staticmethod
    def get_char_high_color(
        bg_color: Tuple[int, int, int],
    ) -> Tuple[int, int, int]:
        r = 140
        d = 20
        if max(*bg_color) > 255 - r:
            r *= -1
        return (
            math.floor(bg_color[0] + d if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] + d if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] + d if bg_color[2] + r <= 255 else 255),
        )

    @staticmethod
    def get_bg_detail_color(
        bg_color: Tuple[int, int, int],
    ) -> Tuple[int, int, int]:
        r = 140
        if max(*bg_color) > 255 - r:
            r *= -1
        return (
            math.floor(bg_color[0] - 20 if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] - 20 if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] - 20 if bg_color[2] + r <= 255 else 255),
        )

    @staticmethod
    def get_highlight_color(
        color: Tuple[int, int, int],
    ) -> Tuple[int, int, int]:
        red_color = color[0]
        green_color = color[1]
        blue_color = color[2]

        highlight_color = {
            "red": red_color - 127 if red_color > 127 else 127,
            "green": green_color - 127 if green_color > 127 else 127,
            "blue": blue_color - 127 if blue_color > 127 else 127,
        }

        max_color = max(highlight_color.values())

        name = ""
        for _highlight_color in highlight_color:
            if highlight_color[_highlight_color] == max_color:
                name = str(_highlight_color)

        if name == "red":
            return red_color, highlight_color["green"], highlight_color["blue"]
        if name == "green":
            return highlight_color["red"], green_color, highlight_color["blue"]
        if name == "blue":
            return highlight_color["red"], highlight_color["green"], blue_color
        return 0, 0, 0  # Error
