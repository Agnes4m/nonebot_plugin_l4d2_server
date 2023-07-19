import base64
import io
from typing import Optional
from nonebot_plugin_txt2img import Txt2Img
from .config import l4_config
from nonebot_plugin_saa import MessageFactory,Image,Text

l4_font = l4_config.l4_font
"""直接超的智障回复"""


def mode_txt_to_img(
    title: str,
    text: str,
    ex_text:Optional[str] = None,
    font_size: int = 32,
    ex_msg:Optional[str] = None
):
    txt2img = Txt2Img()
    txt2img.set_font_size(font_size)
    pic = txt2img.draw(title, text) # 获得base64对象str
    pic = base64.b64decode(pic)
    img_io = io.BytesIO()
    img_io.write(pic)
    img_io.seek(0)
    if not ex_msg:
        msg = MessageFactory([Image(img_io)])
    else:
        msg = MessageFactory([Image(image=img_io),Text(text=ex_msg)]) 
    
    return msg
