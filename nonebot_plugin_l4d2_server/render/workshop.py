"""Workshop info-card HTML rendering."""

from __future__ import annotations

import re
from pathlib import Path

from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_htmlrender import template_to_pic as t2p

from nonebot_plugin_l4d2_server.api import L4API
from nonebot_plugin_l4d2_server.consts import RENDER_TEMPLATES_PATH

from .images import convert_duration  # noqa: F401  (re-export for compat)


async def format_text_to_html(text: str) -> str:
    """Convert BBCode-lite description to HTML paragraphs."""
    html_parts: list[str] = []
    paragraphs = re.split(r"\r?\n\r?\n", text.strip())

    for para in paragraphs:
        if not para.strip():
            continue
        title_match = re.match(r"^\s*~{\s*(.*?)\s*}~\s*$", para)
        if title_match:
            html_parts.append(
                f'<h2 class="adjustable-heading">{title_match.group(1)}</h2>',
            )
            continue
        if para.lstrip().startswith("- "):
            list_items: list[str] = []
            for line in para.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    list_items.append(f"<li>{line[2:].strip()}</li>")
                elif line and list_items:
                    list_items[-1] = list_items[-1].replace(
                        "</li>",
                        f"<br>{line.strip()}</li>",
                    )
            html_parts.append(f"<ul>{''.join(list_items)}</ul>")
            continue
        processed = re.sub(
            r"\[url=([^\]]+)\]([^\[]+)\[/url\]",
            r'<a href="\1" target="_blank">\2</a>',
            para,
        )
        processed = " ".join(processed.split())
        processed = processed.replace("\n", "<br>")
        html_parts.append(f"<p>{processed}</p>")

    return "\n".join(html_parts)


async def _format_timestamp(ts: int) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


async def render_workshop_card(workshop_id: str) -> dict:
    """Fetch workshop info, send the rendered card to chat, return raw dict."""
    info = await L4API.workshops(workshop_id)
    info["time_created"] = await _format_timestamp(info["time_created"])
    info["time_updated"] = await _format_timestamp(info["time_updated"])
    info["file_description"] = await format_text_to_html(info["file_description"])
    info["filename"] = info["filename"].split("/")[-1]

    img_bytes = await t2p(
        template_path=Path(RENDER_TEMPLATES_PATH),
        template_name="workshop.html",
        templates={"info": info},
    )
    await UniMessage.image(raw=img_bytes).send()
    return info
