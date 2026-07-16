from pathlib import Path
from urllib.parse import parse_qs, urlparse

from loguru import logger
from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_htmlrender import template_to_pic as t2p

from ...shared.utils.api.request import L4API
from .utils import format_text_to_html, timestamp_to_date


async def process_ws_download(workshop: str) -> str:
    """解析工坊输入并返回 workshop_id"""
    if workshop.isdigit():
        return workshop
    if workshop.startswith("https://steamcommunity.com/sharedfiles/filedetails"):
        parsed = urlparse(workshop)
        params = parse_qs(parsed.query)
        if "id" in params and params["id"][0].isdigit():
            return params["id"][0]
    return await UniMessage.text("无效的steam链接，请输入工坊ID或完整URL").finish()  # noqa: RET503


async def render_workshop_info(workshop_id: str):
    """获取工坊信息并返回 WorksopInfo"""
    wj = await L4API.workshops(workshop_id)
    wj["time_created"] = await timestamp_to_date(wj["time_created"])
    wj["time_updated"] = await timestamp_to_date(wj["time_updated"])
    wj["file_description"] = await format_text_to_html(wj["file_description"])
    wj["filename"] = wj["filename"].split("/")[-1]
    logger.debug(wj)

    msg = await t2p(
        template_path=Path(__file__).parent.parent / "presentation/render/img/template",
        template_name="workshop.html",
        templates={"info": wj},
    )
    await UniMessage.image(raw=msg).send()
    return wj
