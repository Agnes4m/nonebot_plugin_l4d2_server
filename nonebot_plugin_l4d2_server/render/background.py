"""Background image selection: custom user PNGs/JPGs or pure-white fallback."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Optional, Tuple, cast

from httpx import get
from PIL import Image

from ..consts import CUSTOM_BACKGROUNDS_PATH

# Auto-create user's directory.
CUSTOM_BACKGROUNDS_PATH.mkdir(parents=True, exist_ok=True)


def _list_custom_backgrounds() -> list[Path]:
    """All user-placed backgrounds (PNG/JPG/JPEG)."""
    return (
        list(CUSTOM_BACKGROUNDS_PATH.glob("*.png"))
        + list(CUSTOM_BACKGROUNDS_PATH.glob("*.jpg"))
        + list(CUSTOM_BACKGROUNDS_PATH.glob("*.jpeg"))
    )


def pick_background(
    url: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Image.Image:
    """Return a background image, optionally sized to fit.

    Priority: explicit URL > random user background > pure white.
    """
    if url:
        return Image.open(get(url).content).convert("RGBA")

    files = _list_custom_backgrounds()
    if files:
        chosen = random.choice(files)
        try:
            return Image.open(chosen).convert("RGBA")
        except Exception as exc:
            print(f"打开自定义背景失败: {chosen.name}: {exc}")

    if width and height:
        return Image.new("RGBA", (width, height), (255, 255, 255, 255))

    return Image.new("RGBA", (1, 1), (255, 255, 255, 255))


def crop_to(img: Image.Image, w: int, h: int) -> Image.Image:
    """Crop ``img`` to ``w x h`` keeping aspect ratio (centered)."""
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


def dominant_color(img: Image.Image) -> Tuple[int, int, int]:
    """Sample the most common color in ``img`` (after quantize)."""
    small = img.copy().convert("RGBA").resize((1, 1), resample=0)
    pixel = small.getpixel((0, 0))
    return cast(Tuple[int, int, int], pixel[:3])
