"""Single-server card renderer (PIL image or plain text)."""

from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

from a2s import Player
from PIL import Image, ImageDraw, ImageFont

from ..config import config
from ..messages import Sm as MsgSm

# 单张图片宽度（像素），超长行会按像素宽度自动换行
MAX_CARD_WIDTH = 380
MARGIN = 16
LINE_SPACING = 7
MIN_HEIGHT = 300
FONT_SIZE = 18

# 单服务器卡底色（/云1 这种具体服查询固定用纯色，方便阅读）
DEFAULT_CARD_BG_COLOR = (73, 109, 137)


def _resolve_card_background(img_w: int, img_h: int) -> Image.Image:
    """单服务器卡固定使用纯色背景，不加载任何图片。"""
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
    """Format seconds as ``Hh Mm Ss`` (zero components omitted)."""
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
    """Rendered pixel width of ``text``."""
    return font.getbbox(text)[2]


def _wrap_line(line: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """按像素宽度把一行拆成多行；单字符超宽时也保留为单字符行避免死循环。"""
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
            if _measure(font, line[pos:end]) > max_width:
                break
            best = end
            end += 1
        if best == pos:
            best = pos + 1  # 单字符超宽，强制推进避免死循环
        chunks.append(line[pos:best])
        pos = best
    return chunks


def _wrap_lines(
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """对一组行做按像素宽度的换行，返回扁平行列表。"""
    out: list[str] = []
    for line in lines:
        out.extend(_wrap_line(line, font, max_width))
    return out


# 标签前缀 → 值颜色。VAC 行的颜色按启用/禁用动态计算。
_VALUE_COLORS: dict[str, tuple[int, int, int]] = {
    "游戏: ": (200, 180, 255),
    "地图: ": (166, 202, 253),
    "人数: ": (100, 255, 100),
    "延迟: ": (100, 255, 100),
    "类型: ": (180, 220, 255),
    "密码: ": (255, 255, 255),
}
_VAC_PREFIX = "VAC : "
_VAC_COLOR = (70, 209, 110)
_VAC_OFF_COLOR = (255, 90, 90)


def _value_color(line: str) -> tuple[int, int, int] | None:
    """行值部分应使用的颜色；不匹配任何前缀则返回 None。"""
    for prefix, color in _VALUE_COLORS.items():
        if line.startswith(prefix):
            return color
    if line.startswith(_VAC_PREFIX):
        return (
            _VAC_COLOR if line[len(_VAC_PREFIX) :].strip() == "启用" else _VAC_OFF_COLOR
        )
    return None


def _draw_label_value(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
    line: str,
    prefix: str,
    x: int,
    y: int,
    value_color: tuple[int, int, int],
) -> None:
    """绘制「白色标签 + 彩色值」一行。"""
    draw.text((x, y), prefix, font=font, fill=(255, 255, 255))
    draw.text(
        (x + _measure(font, prefix), y),
        line[len(prefix) :].strip(),
        font=font,
        fill=value_color,
    )


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


def _build_card_text(server, players, host, port) -> tuple[str, str]:
    """构造卡片要绘制的文本：返回 ``(title, content)``。"""
    title = f"-{server.server_name}-"
    content_lines = [
        f"游戏: {server.folder}",
        f"地图: {server.map_name}",
        f"人数: {server.player_count} / {server.max_players}",
    ]
    if server.ping is not None:
        vac = "启用" if server.vac_enabled else "禁用"
        content_lines.append(f"延迟: {server.ping * 1000:.0f} ms")
        content_lines.append(f"VAC : {vac}")
        content_lines.append("")  # 空行
        content_lines.append(_format_player_lines(players).rstrip("\n"))
    if config.l4_show_ip:
        content_lines.append("")
        content_lines.append(f"connect {host}:{port}")
    return title, "\n".join(content_lines)


def _render_server_image(server, players, host, port) -> bytes | None:
    """Render a styled PIL card. Returns PNG bytes or ``None`` on bg failure.

    长内容（服务器名、connect IP 等）会按 ``MAX_CARD_WIDTH - 2 * MARGIN``
    的像素宽度自动换行，图片高度按行数自动撑高。
    """
    font = _load_font(FONT_SIZE)
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]

    title_raw, content_raw = _build_card_text(server, players, host, port)
    text_max_w = MAX_CARD_WIDTH - 2 * MARGIN
    title_lines = _wrap_line(title_raw, font, text_max_w)
    content_lines = _wrap_lines(content_raw.split("\n"), font, text_max_w)

    title_heights = [
        font.getbbox(line)[3] - font.getbbox(line)[1] for line in title_lines
    ]
    title_widths = [_measure(font, line) for line in title_lines]
    title_total_h = sum(title_heights) + LINE_SPACING * max(0, len(title_lines) - 1)
    content_height = (
        len(content_lines) * (line_height + LINE_SPACING) - LINE_SPACING
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
        MIN_HEIGHT,
    )

    draw = ImageDraw.Draw(_resolve_card_background(img_w, int(img_h)))

    # 标题：多行居中
    title_y = MARGIN
    for idx, line in enumerate(title_lines):
        draw.text(
            ((img_w - title_widths[idx]) // 2, title_y),
            line,
            font=font,
            fill=(255, 255, 255),
        )
        title_y += title_heights[idx] + LINE_SPACING

    content_y = title_y + (MARGIN if content_lines else 0) - LINE_SPACING
    content_x = MARGIN

    for line in content_lines:
        if (color := _value_color(line)) is not None:
            prefix = (
                _VAC_PREFIX
                if line.startswith(_VAC_PREFIX)
                else next(p for p in _VALUE_COLORS if line.startswith(p))
            )
            _draw_label_value(draw, font, line, prefix, content_x, content_y, color)
        else:
            draw.text((content_x, content_y), line, font=font, fill=(255, 255, 255))
        content_y += line_height + LINE_SPACING

    buf = io.BytesIO()
    draw._image.save(buf, format="PNG")  # noqa: SLF001
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
