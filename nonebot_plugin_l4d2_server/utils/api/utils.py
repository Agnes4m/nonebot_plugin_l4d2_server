from typing import Union

from nonebot_plugin_alconna import UniMessage


async def out_msg_out(
    msg: Union[str, bytes, UniMessage],
    is_connect: bool = False,
    host: str = "",
    port: str = "",
):
    """
    统一消息输出函数

    Args:
        msg: 要输出的消息内容
        is_connect: 是否为连接消息
        host: 服务器地址
        port: 服务器端口
    """
    if isinstance(msg, UniMessage):
        return await msg.finish()
    if isinstance(msg, str):
        await UniMessage.text(msg).finish()
    if is_connect:
        out = UniMessage.image(raw=msg) + UniMessage.text(
            f"connect: {host}:{port}",
        )
        return await out.finish()
    return await UniMessage.image(raw=msg).finish()
