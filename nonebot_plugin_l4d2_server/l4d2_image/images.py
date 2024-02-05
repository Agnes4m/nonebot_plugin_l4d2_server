import sys
from base64 import b64encode
from io import BytesIO
from pathlib import Path
from typing import Union, overload

import aiofiles
from PIL import Image

MAIN_PATH = Path() / "data" / "GenshinUID"
sys.path.append(str(MAIN_PATH))
CONFIG_PATH = MAIN_PATH / "config.json"
RESOURCE_PATH = MAIN_PATH / "resource"
WIKI_PATH = MAIN_PATH / "wiki"
CU_BG_PATH = MAIN_PATH / "bg"
CU_CHBG_PATH = MAIN_PATH / "chbg"
WEAPON_PATH = RESOURCE_PATH / "weapon"
GACHA_IMG_PATH = RESOURCE_PATH / "gacha_img"
CHAR_PATH = RESOURCE_PATH / "chars"
CHAR_STAND_PATH = RESOURCE_PATH / "char_stand"
CHAR_SIDE_PATH = RESOURCE_PATH / "char_side"
CHAR_NAMECARD_PATH = RESOURCE_PATH / "char_namecard"
REL_PATH = RESOURCE_PATH / "reliquaries"
ICON_PATH = RESOURCE_PATH / "icon"
TEMP_PATH = RESOURCE_PATH / "temp"
CARD_PATH = RESOURCE_PATH / "card"
GUIDE_PATH = WIKI_PATH / "guide"
TEXT2D_PATH = Path(__file__).parents[2] / "resource" / "texture2d"

PLAYER_PATH = MAIN_PATH / "players"


TEXT2D_PATH = Path(__file__).parents[2] / "resource" / "texture2d"
FETTER_PATH = TEXT2D_PATH / "fetter"
TALENT_PATH = TEXT2D_PATH / "talent"
WEAPON_BG_PATH = TEXT2D_PATH / "weapon"
WEAPON_AFFIX_PATH = TEXT2D_PATH / "weapon_affix"
LEVEL_PATH = TEXT2D_PATH / "level"

BG_PATH = Path(__file__).parent / "bg"
TEXT_PATH = Path(__file__).parent / "texture2d"
ring_pic = Image.open(TEXT_PATH / "ring.png")
mask_pic = Image.open(TEXT_PATH / "mask.png")
NM_BG_PATH = BG_PATH / "nm_bg"
SP_BG_PATH = BG_PATH / "sp_bg"

bg_path = CU_BG_PATH if list(CU_BG_PATH.iterdir()) != [] else NM_BG_PATH


@overload
async def convert_img(img: Image.Image, is_base64: bool = False) -> bytes: ...


@overload
async def convert_img(img: Image.Image, is_base64: bool = True) -> str: ...


@overload
async def convert_img(img: bytes, is_base64: bool = False) -> str: ...


@overload
async def convert_img(img: Path, is_base64: bool = False) -> str: ...


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
    if isinstance(img, Image.Image):
        img = img.convert("RGB")
        result_buffer = BytesIO()
        img.save(result_buffer, format="PNG", quality=80, subsampling=0)
        res = result_buffer.getvalue()
        if is_base64:
            res = "base64://" + b64encode(res).decode()
        return res
    if isinstance(img, bytes):
        pass
    else:
        async with aiofiles.open(img, "rb") as fp:
            img = await fp.read()
    return f"[CQ:image,file=base64://{b64encode(img).decode()}]"
