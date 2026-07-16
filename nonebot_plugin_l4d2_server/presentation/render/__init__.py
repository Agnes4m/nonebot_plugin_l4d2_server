from typing import List

from ...shared.utils.api.models import OutServer
from .html_img import server_ip_pic


async def msg_to_image(server_dict: List[OutServer], mode_: str = "html"):
    if mode_ == "html":
        return await server_ip_pic(server_dict)
    return None
