from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_txt2img import Txt2Img
from .config import l4_config

l4_font = l4_config.l4_font
"""直接超的智障回复"""


def mode_txt_to_img(
    title: str,
    text: str,
    font_size: int = 32,
):
    txt2img = Txt2Img()
    txt2img.set_font_size(font_size)
    pic = txt2img.draw(title, text)
    msg = MessageSegment.image(pic)
    return msg
