from pathlib import Path

from nonebot_plugin_l4d2_server.utils.api.models import AnnePlayer2
from PIL import Image, ImageFont

from ..config import config

font = ImageFont.truetype(config.l4_font)

anne_path = Path(__file__).parent / "img" / "anne"


async def anne_player_info(msg: AnnePlayer2):
    back_img = Image.open(anne_path / "back1.jpg")
    base_img = Image.new("RGBA", (back_img.size), (255, 255, 255, 50))
    back_img.paste(base_img, (0, 0), base_img)
    return msg
