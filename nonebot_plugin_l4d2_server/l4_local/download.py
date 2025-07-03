from pathlib import Path

from loguru import logger
from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_htmlrender import template_to_pic as t2p

from ..utils.api.request import L4API
from .utils import format_text_to_html, timestamp_to_date


async def process_ws_download(workshop: str):

    if workshop.isdigit():
        workshop_id = workshop
    elif workshop.startswith("https://steamcommunity.com/sharedfiles/filedetails"):
        workshop_id = workshop.split("/?id=")[-1]
    else:
        await UniMessage.text("无效的steam链接").finish()
    wj = await L4API.workshops(workshop_id)
    wj["time_created"] = await timestamp_to_date(
        wj["time_created"],
    )
    wj["time_updated"] = await timestamp_to_date(
        wj["time_updated"],
    )
    wj["file_description"] = await format_text_to_html(
        wj["file_description"],
    )
    wj["filename"] = wj["filename"].split("/")[-1]

    logger.debug(wj)

    msg = await t2p(
        template_path=Path(__file__).parent.parent / "l4_image/img/template",
        template_name="workshop.html",
        templates={"info": wj},
    )
    await UniMessage.image(raw=msg).send()
    return wj
