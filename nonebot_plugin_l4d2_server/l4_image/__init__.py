from typing import List  # noqa:

from ..utils.api.models import OutServer
from .html_img import server_ip_pic


async def msg_to_image(server_dict: List[OutServer], mode_: str = "html"):
    """信息构造图片"""
    if mode_ == "html":
        """用浏览器作图"""
        return await server_ip_pic(server_dict)
    if mode_ == "pil":
        """用pil作图"""
        return None
    """返回文字"""
    return None
