"""Single-server card renderer. Outputs either a PIL image
(bytes) or a plain text description, depending on ``is_img``.
"""

from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

from a2s import Player
from nonebot.log import logger
from PIL import Image, ImageDraw, ImageFont

from ..config import config
from ..consts import CUSTOM_BACKGROUNDS_PATH
from ..messages import Sm as MsgSm

# 单张图片的目标最大宽度（像素）。长于此宽度的行会被自动换行，
# 避免在 800px 硬上限下文字被背景裁断。
MAX_CARD_WIDTH = 760
MARGIN = 20

# 单服务器卡默认底色（找不到自定义背景时使用）。
DEFAULT_CARD_BG_COLOR = (73, 109, 137)


def _resolve_card_background(img_w: int, img_h: int) -> Image.Image:
    """查找单服务器卡的背景图，找不到则使用默认底色。

    优先 ``data/L4D2/custom_backgrounds/`` 下按文件名排序的第一张图，
    这样用户可以单独为单服务器卡准备一张图。
    """
    if CUSTOM_BACKGROUNDS_PATH.is_dir():
        for bg_path in sorted(CUSTOM_BACKGROUNDS_PATH.iterdir()):
            if bg_path.is_file() and bg_path.suffix.lower() in (
                ".png",
                ".jpg",
                ".jpeg",
            ):
                try:
                    with Image.open(bg_path) as src:
                        return src.convert("RGB").resize((img_w, img_h))
                except Exception as exc:
                    logger.warning(f"加载自定义背景 {bg_path.name} 失败: {exc}")
                    break
    return Image.new("RGB", (img_w, img_h), DEFAULT_CARD_BG_COLOR)


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


def _measure(font: ImageFont.FreeTypeFont, text: str) -> int:
    """Return rendered pixel width of ``text``."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def _wrap_line(line: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """按像素宽度将一行文字拆成多行。

    单个字符宽度超过 ``max_width`` 时也会被保留为单字符一行，避免死循环。
    """
    if not line:
        return [""]
    if _measure(font, line) <= max_width:
        return [line]

    chunks: list[str] = []
    pos = 0
    n = len(line)
    while pos < n:
        best = pos
        end = best + 1
        while end <= n:
            w = _measure(font, line[pos:end])
            if w > max_width:
                break
            best = end
            end += 1
        if best == pos:
            # 当前单个字符就超宽；强行保留单字符避免死循环
            best = pos + 1
        chunks.append(line[pos:best])
        pos = best
    return chunks


def _wrap_lines(
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """对一组行做按像素宽度的换行，返回新的扁平行列表。"""
    out: list[str] = []
    for line in lines:
        out.extend(_wrap_line(line, font, max_width))
    return out


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
    """Render a styled PIL card. Returns JPEG bytes or ``None`` on bg failure.

    长内容（服务器名、connect IP 等）会按 ``MAX_CARD_WIDTH - 2 * MARGIN``
    的像素宽度自动换行，避免被 800px 背景裁断。
    """
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
            f"延迟: {server.ping * 1000:.0f} ms\nVAC : {vac_status}\n\n{player_info}"
        )
    if config.l4_show_ip:
        text += f"\nconnect {host}:{port}"

    raw_lines = text.split("\n")
    raw_title = raw_lines[0]
    raw_content = raw_lines[1:]

    text_max_w = MAX_CARD_WIDTH - 2 * MARGIN
    title_lines = _wrap_line(raw_title, font, text_max_w)
    content_lines = _wrap_lines(raw_content, font, text_max_w)

    line_spacing = 7
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    title_heights = [
        font.getbbox(line)[3] - font.getbbox(line)[1] for line in title_lines
    ]
    title_total_h = sum(title_heights) + line_spacing * max(0, len(title_lines) - 1)
    title_widths = [_measure(font, line) for line in title_lines]
    content_height = (
        len(content_lines) * (line_height + line_spacing) - line_spacing
        if content_lines
        else 0
    )

    img_w = MAX_CARD_WIDTH
    img_h = max(
        MARGIN
        + title_total_h
        + (MARGIN if content_lines else 0)
        + content_height
        + MARGIN,
        300,
    )

    bg = _resolve_card_background(img_w, int(img_h))
    draw = ImageDraw.Draw(bg)

    # 标题：多行居中
    title_y = MARGIN
    for idx, line in enumerate(title_lines):
        line_w = title_widths[idx]
        draw.text(
            ((img_w - line_w) // 2, title_y),
            line,
            font=font,
            fill=(255, 255, 255),
        )
        title_y += title_heights[idx] + line_spacing

    content_y = title_y + (MARGIN if content_lines else 0) - line_spacing
    content_x = MARGIN

    value_colors = {
        "游戏: ": (200, 180, 255),
        "地图: ": (166, 202, 253),
        "人数: ": (100, 255, 100),
        "延迟: ": (100, 255, 100),
        "类型: ": (180, 220, 255),
        "密码: ": (255, 255, 255),
    }
    for line in content_lines:
        colored = False
        for prefix, color in value_colors.items():
            if line.startswith(prefix):
                prefix_w = _measure(font, prefix)
                draw.text(
                    (content_x, content_y),
                    prefix,
                    font=font,
                    fill=(255, 255, 255),
                )
                draw.text(
                    (content_x + prefix_w, content_y),
                    line[len(prefix) :].strip(),
                    font=font,
                    fill=color,
                )
                colored = True
                break
        if not colored and line.startswith("VAC :"):
            prefix = "VAC : "
            prefix_w = _measure(font, prefix)
            draw.text(
                (content_x, content_y),
                prefix,
                font=font,
                fill=(255, 255, 255),
            )
            vac_value = line[len(prefix) :].strip()
            vac_color = (70, 209, 110) if vac_value == "启用" else (255, 90, 90)
            draw.text(
                (content_x + prefix_w, content_y),
                vac_value,
                font=font,
                fill=vac_color,
            )
            colored = True
        if not colored:
            draw.text(
                (content_x, content_y),
                line,
                font=font,
                fill=(255, 255, 255),
            )
        content_y += line_height + line_spacing

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
