from typing import List

from ..utils.api.models import OutServer
from .html_img import server_ip_pic

# from nonebot_plugin_alconna import At, UniMsg, on_alconna, Reply

# ts = on_alconna(
#     "ts",
#     aliases={"测试"},
#     block=True,
# )


# @ts.handle()
# async def _(event: Event):
#     msg = event.model_dump()
#     for msg_seg in msg:
#         if msg_seg.type == "image":
#             usrid = await at_to_usrid(msg_seg.data["qq"])
#             if usrid:
#                 await ts.send(f"[CQ:at,qq={usrid}]")
#                 break


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
