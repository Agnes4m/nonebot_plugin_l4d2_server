"""Single-server card renderer.

Replaces ``server/query/draw_msg.draw_one_ip``. Outputs either a PIL image
(bytes) or a plain text description, depending on ``is_img``.
"""

from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from a2s import Player
from nonebot.log import logger

from config import config  # noqa: F401  (config injected by app at runtime)
from messages import Sm as MsgSm
from .images import convert_duration

# Background image bundled inside the plugin.
BG_PATH = (
    Path(__file__).parent / "backgrounds" / "anne" / "back.png"
)


@lru_cache(maxsize=16)
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Cached font loader, falling back through system fonts."""
    candidates = [
        str(Path(__file__).parent / "fonts" / "loli.ttf"),
        "msyh.ttc",
        "simhei.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _format_player_lines(players: list[Player]) -> str:
    if not players:
        return "服务器感觉很安静啊\n"
    max_duration = max(len(str(_format_dur(p.duration))) for p in players)
    max_score = max(len(str(p.score)) for p in players)
    lines: list[str] = []
    for p in players:
        score = "[{:>{}}]".format(p.score, max_score)
        dur = "{:^{}}".format(_format_dur(p.duration), max_duration)
        name = str(p.name).strip()
        lines.append(f"{score} | {dur} | {name[:15]}")
    return "\n".join(lines) + "\n"


def _format_dur(seconds: float) -> str:
    """Synchronous version used in plain text context."""
    total = int(seconds)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    out = ""
    if h:
        out += f"{h}h "
    if m:
        out += f"{m}m "
    return out + f"{s}s"


def _build_text_message(server, host: str, port: int) -> str:
    """Plain-text server description (no image)."""
    vac = "启用" if server.vac_enabled else "禁用"
    msg = (
        f"-{server.server_name}-\n"
        f"游戏: {server.folder}\n"
        f"地图: {server.map_name}\n"
        f"人数: {server.player_count} / {server.max_players}"
    )
    if server.ping is not None:
        msg += f"\n延迟: {server.ping * 1000:.0f} ms\nVAC : {vac}\n"
    if config.l4_show_ip:
        msg += f"\nconnect {host}:{port}"
    return msg


def _render_server_image(server, players, host, port) -> bytes | None:
    """Render a styled PIL card. Returns JPEG bytes or ``None`` on bg failure."""
    font = _load_font(18)
    vac_status = "启用" if server.vac_enabled else "禁用"
    player_info = _format_player_lines(players)
    text = (
        f"-{server.server_name}-\n"
        f"游戏: {server.folder}\n"
        f"地图: {server.map_name}\n"
        f"人数: {server.player_count} / {server.max_players}\n"
    )
    if server.ping is not None:
        text += (
            f"延迟: {server.ping * 1000:.0f} ms\n"
            f"VAC : {vac_status}\n\n"
            f"{player_info}"
        )
    if config.l4_show_ip:
        text += f"\nconnect {host}:{port}"

    lines = text.split("\n")
    title = lines[0]
    content = "\n".join(lines[1:]) if len(lines) > 1 else ""

    title_bbox = font.getbbox(title)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]

    margin = 20
    line_spacing = 7
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    content_lines = content.split("\n") if content else []
    content_height = len(content_lines) * line_height if content_lines else 0
    content_width = (
        max(font.getbbox(l)[2] - font.getbbox(l)[0] for l in content_lines)
        if content_lines
        else 0
    )

    img_w = max(title_w, content_width) + 2 * margin
    img_h = max(
        title_h + content_height
        + (line_spacing + 1) * max(0, len(content_lines) - 1)
        + 2 * margin,
        300,
    )

    title_x = (img_w - title_w) // 2
    title_y = margin
    content_y = title_y + title_h + margin if content else 0
    content_x = margin

    try:
        bg = Image.open(BG_PATH).resize(
            (min(img_w, 800), int(img_h)),
        )
        draw = ImageDraw.Draw(bg)
    except Exception as exc:
        logger.error(f"加载背景图片失败: {exc}")
        bg = Image.new("RGB", (img_w, img_h), (73, 109, 137))
        draw = ImageDraw.Draw(bg)

    draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255))

    value_colors = {
        "游戏: ": (200, 180, 255),
        "地图: ": (166, 202, 253),
        "人数: ": (100, 255, 100),
        "延迟: ": (100, 255, 100),
        "类型: ": (180, 220, 255),
        "密码: ": (255, 255, 255),
    }
    if content:
        current_y = content_y
        for line in content_lines:
            colored = False
            for prefix, color in value_colors.items():
                if line.startswith(prefix):
                    prefix_w = font.getbbox(prefix)[2] - font.getbbox(prefix)[0]
                    draw.text(
                        (content_x, current_y),
                        prefix,
                        font=font,
                        fill=(255, 255, 255),
                    )
                    draw.text(
                        (content_x + prefix_w, current_y),
                        line[len(prefix):].strip(),
                        font=font,
                        fill=color,
                    )
                    colored = True
                    break
            if not colored and line.startswith("VAC :"):
                prefix = "VAC : "
                prefix_w = font.getbbox(prefix)[2] - font.getbbox(prefix)[0]
                draw.text(
                    (content_x, current_y),
                    prefix,
                    font=font,
                    fill=(255, 255, 255),
                )
                vac_value = line[len(prefix):].strip()
                vac_color = (70, 209, 110) if vac_value == "启用" else (255, 90, 90)
                draw.text(
                    (content_x + prefix_w, current_y),
                    vac_value,
                    font=font,
                    fill=vac_color,
                )
                colored = True
            if not colored:
                draw.text(
                    (content_x, current_y),
                    line,
                    font=font,
                    fill=(255, 255, 255),
                )
            current_y += line_height + line_spacing

    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    return buf.getvalue()


async def render_server_card(
    server,
    players: list[Player],
    host: str,
    port: int,
    *,
    is_img: bool,
) -> str | bytes:
    """Render single-server output. Returns bytes for image mode or str otherwise."""
    if not is_img:
        return _build_text_message(server, host, port)
    return _render_server_image(server, players, host, port) or MsgSm.server_outtime