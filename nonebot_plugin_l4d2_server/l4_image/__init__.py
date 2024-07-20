from typing import Dict, List, Optional, Tuple

import a2s

from ..utils.api.models import OutServer
from .html_img import server_ip_pic


async def msg_to_image(server_dict: List[OutServer], mode = "html"):
    """信息构造图片"""
    if mode == "html":
        """用浏览器作图"""
        return await server_ip_pic(server_dict)
    elif mode == "pil":
        """用pil作图"""
    else:
        """返回文字"""