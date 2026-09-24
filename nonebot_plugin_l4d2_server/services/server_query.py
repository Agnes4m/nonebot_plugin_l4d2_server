"""Server query service: A2S queries, single-server output, group summaries."""

from __future__ import annotations

import re
import time
from functools import lru_cache
from typing import AsyncIterator, List, Optional, Tuple, cast

from nonebot.log import logger

from ..api import L4API, AllServer, OutServer
from ..config import config
from ..http_helpers import split_maohao
from ..messages import Sm as MsgSm
from ..messages import split_message
from ..registry import registry
from ..render import render_server_card, render_server_list, render_text_card


async def query_group_servers(group_name: str) -> List[OutServer]:
    """Query A2S info for every server in ``group_name``."""
    servers = registry.get(group_name)
    if not servers:
        return []

    ip_list: List[Tuple[str, int]] = [(s["host"], int(s["port"])) for s in servers]
    results = await L4API.a2s_info_batch(ip_list)

    # Pad missing entries with empty SourceInfo for stable indexing.
    out: List[OutServer] = []
    for (server, players), srv in zip(results, servers):
        out.append(
            cast(
                OutServer,
                {
                    "server": server,
                    "player": players,
                    "host": srv["host"],
                    "port": srv["port"],
                    "command": group_name,
                    "id_": srv["id"],
                    "name": display_name(server.server_name),
                },
            ),
        )
    return out


@lru_cache(maxsize=4)
def _name_prefix_re(pattern: str) -> Optional[re.Pattern[str]]:
    if not pattern:
        return None
    try:
        return re.compile(pattern)
    except re.error as exc:
        logger.warning(f"[l4] l4_name_strip_pattern 不是合法正则，已忽略: {exc}")
        return None


def display_name(server_name: str) -> str:
    """列表里显示的服务器名：去掉 ``l4_name_strip_pattern`` 匹配的前缀。

    默认把 ``Anne云服#57[普通药役][8特20秒]`` 显示成 ``[普通药役][8特20秒]``——
    卡片前面已经有 ``云57:``，前缀只会把模式 / 特感信息挤成省略号。
    去完为空时（名字只有前缀）保留原名。
    """
    pattern = _name_prefix_re(config.l4_name_strip_pattern)
    if pattern is None:
        return server_name
    return pattern.sub("", server_name, count=1).strip() or server_name


def _calc_stats(servers: List[OutServer]) -> Tuple[int, int, int, int]:
    active = [s for s in servers if s["server"].max_players != 0]
    return (
        len(active),
        len(servers),
        sum(s["server"].player_count for s in active),
        sum(s["server"].max_players for s in active),
    )


def _format_summary(items: List[AllServer]) -> str:
    return "\n".join(
        f"{s['command']} | 服务器{s['active_server']}/{s['max_server']} | "
        f"玩家{s['active_player']}/{s['max_player']}"
        for s in items
        if s["max_player"]
    )


async def get_all_server_detail() -> str:
    """Aggregated summary across every loaded group."""
    items: List[AllServer] = []
    for group in registry.group_names:
        servers = await query_group_servers(group)
        if not servers:
            continue
        active, total, active_p, max_p = _calc_stats(servers)
        items.append(
            cast(
                AllServer,
                {
                    "command": group,
                    "active_server": active,
                    "max_server": total,
                    "active_player": active_p,
                    "max_player": max_p,
                },
            ),
        )
    return _format_summary(items)


async def get_server_detail(
    command: str,
    server_id: str,
    *,
    is_img: bool = True,
) -> str | bytes | None:
    """Render a single server of ``command`` group; ``None`` = 组或 id 不存在。"""
    endpoint = find_endpoint(command, server_id)
    if endpoint is None:
        return None
    host, port = endpoint
    return await _render_single(host, port, is_img)


async def iter_group_output(
    command: str,
    *,
    is_img: bool = True,
    show_all: bool = False,
) -> AsyncIterator[bytes | str]:
    """组查询输出，逐条产出（一页一张图 / 一段一条文字），调用方逐条发送。

    - 默认（``云``）只列有人的服务器；``show_all``（``云全``）列出全部在线服，
      并在最后一页附上不在线列表。
    - 图片：要列的服按 ``l4_image_page_size`` 分页，每页单独出图。一张装下
      上百台的长图超过 16384px 会被 Chromium 截断，也更容易超时 / OOM、
      在 QQ 里缩成看不清的长条；分页后每张 2400px 左右。
    - 某页 Chromium 出图失败后，这一页和本次查询后面的页都改用纯 PIL
      简易图，不再每页各等一次超时。
    - 文字（``l4_image`` 关闭）：每台一行，按消息长度切成多条。

    组不存在或为空时什么都不产出；默认模式下一台有人的都没有时只产出一句提示。
    """
    t_total = time.perf_counter()
    out_servers = await query_group_servers(command)
    if not out_servers:
        return
    a2s_ms = (time.perf_counter() - t_total) * 1000

    # A2S 失败时 ``server.max_players == 0`` 作 sentinel：在线画卡片，离线写文字区。
    online = [s for s in out_servers if s["server"].max_players != 0]
    active = [s for s in online if s["server"].player_count > 0]
    offline_ids = [
        f"{s['command']}{s['id_']}" for s in out_servers if s["server"].max_players == 0
    ]
    counts = f"在线 {len(online)}/{len(out_servers)} 台"
    if show_all:
        heading = f"已加载服务器 {command} ({counts})"
        hint = ""
    elif active:
        heading = f"{command} 有人的服务器 {len(active)} 台 ({counts})"
        hint = f"只显示有人的服务器，发送「{command}全」查看全部"
    else:
        yield f"{command} 现在没有有人的服务器（{counts}），发送「{command}全」查看全部"
        return

    if not is_img:
        logger.info(
            f"[l4] {command} 组查询：{len(out_servers)} 服 / "
            f"A2S {a2s_ms:.0f}ms（仅文字模式）",
        )
        listed = out_servers if show_all else active
        lines = [heading, *([hint] if hint else []), *map(_server_line, listed)]
        for chunk in split_message(lines):
            yield chunk
        return

    cards = online if show_all else active
    # 按服务器数硬阈值跳走图片（光 server 可设 ``L4_IMAGE_MAX_SERVERS``
    # 避免 Chromium OOM）。超过阈值时直接发简短提示，不出文字汇总——
    # 用户场景就是看图，文字堆没意义。
    max_servers = int(config.l4_image_max_servers)
    if max_servers > 0 and len(cards) > max_servers:
        logger.info(
            f"[l4] {command} 组查询：要画 {len(cards)} 服 > "
            f"l4_image_max_servers={max_servers}，跳过图片",
        )
        yield (
            f"⚠️ 组「{command}」要显示的服务器 {len(cards)} 台超过 "
            f"l4_image_max_servers={max_servers}，跳过图片。"
            f"如需查看请用 {command}<序号> 查单台。"
        )
        return

    size = int(config.l4_image_page_size)
    pages = [cards[i : i + size] for i in range(0, len(cards), size)] or [[]]
    use_browser = True
    for no, chunk in enumerate(pages, start=1):
        t_page = time.perf_counter()
        title = heading + (f" · 第 {no}/{len(pages)} 页" if len(pages) > 1 else "")
        page_offline = offline_ids if show_all and no == len(pages) else []
        pic = None
        if use_browser:
            pic = await render_server_list(
                chunk,
                heading=title,
                hint=hint,
                offline_ids=page_offline,
            )
            if pic is None:
                use_browser = False
                logger.warning(f"[l4] {command} 第 {no} 页浏览器出图失败，改用简易图")
        if pic is None:
            pic = _plain_page(title, hint, chunk, page_offline)
        logger.info(
            f"[l4] {command} 组查询 第 {no}/{len(pages)} 页：{len(chunk)} 服 | "
            f"render {(time.perf_counter() - t_page) * 1000:.0f}ms",
        )
        yield pic
    logger.info(
        f"[l4] {command} 组查询{'（全部）' if show_all else ''}：{len(out_servers)} 服 / "
        f"在线 {len(online)} / 有人 {len(active)} / 不在线 {len(offline_ids)} / "
        f"{len(pages)} 页 | "
        f"A2S {a2s_ms:.0f}ms，总计 {(time.perf_counter() - t_total) * 1000:.0f}ms",
    )


def _server_line(s: OutServer) -> str:
    """一台服一行：编号 / 人数 / 地图放前面，名字最长、放最后。"""
    srv = s["server"]
    if srv.max_players == 0:
        return f"{s['command']}{s['id_']}  离线"
    return (
        f"{s['command']}{s['id_']}  {srv.player_count}/{srv.max_players}  "
        f"{srv.map_name}  {s.get('name') or srv.server_name}"
    )


def _plain_page(
    title: str,
    hint: str,
    servers: List[OutServer],
    offline_ids: List[str],
) -> bytes:
    """浏览器出图失败时的兜底图：纯 PIL，每台服一行。"""
    lines = [*([hint] if hint else []), *map(_server_line, servers)]
    if offline_ids:
        lines.append(f"不在线（{len(offline_ids)} 台）：{' '.join(offline_ids)}")
    return render_text_card(f"{title}（简易图）", lines or ["（没有在线的服务器）"])


async def _render_single(host: str, port: int, is_img: bool) -> bytes | str | None:
    info = await L4API.a2s_info_batch([(host, port)])
    if not info or info[0][0].max_players == 0:
        return MsgSm.server_outtime
    server, players = info[0]
    return await render_server_card(server, players, host, port, is_img=is_img)


def _find_endpoint(servers: list[dict], server_id: str) -> Optional[Tuple[str, int]]:
    for server in servers:
        if str(server_id) == str(server.get("id")):
            return server["host"], int(server["port"])
    return None


def find_endpoint(command: str, server_id: str) -> Optional[Tuple[str, int]]:
    """Look up ``(host, port)`` for a specific server id in ``command`` group.

    返回 ``None`` 表示该组不存在或组里没有匹配 ``server_id`` 的服务器。
    """
    servers = registry.get(command)
    if not servers:
        return None
    return _find_endpoint(servers, server_id)


async def get_ip_server(ip: str) -> bytes | str:
    """Render a server by raw ``host:port``."""
    host, port = split_maohao(ip)
    info = await L4API.a2s_info_batch([(host, port)])
    if not info or info[0][0].max_players == 0:
        return MsgSm.server_outtime
    server, players = info[0]
    return await render_server_card(server, players, host, port, is_img=config.l4_image)
