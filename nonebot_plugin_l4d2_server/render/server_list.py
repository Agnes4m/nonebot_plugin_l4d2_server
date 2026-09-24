"""Server-list HTML rendering via nonebot_plugin_htmlrender."""

from __future__ import annotations

import asyncio
from typing import Optional

from a2s.players import Player
from jinja2 import Environment, FileSystemLoader
from nonebot.log import logger
from nonebot_plugin_htmlrender import html_to_pic

from ..config import config
from ..consts import RENDER_BACKGROUNDS_PATH, RENDER_TEMPLATES_PATH
from .background import pick_random_user_background
from .images import convert_duration

_template_env: Environment | None = None

# 同一时刻只让 Chromium 出一张图：多人同时查大组时并发开页面，
# 小内存机器上 Chromium 会被 OOM killer 杀掉。
_render_lock = asyncio.Lock()


def _get_env() -> Environment:
    global _template_env
    if _template_env is None:
        _template_env = Environment(
            loader=FileSystemLoader(str(RENDER_TEMPLATES_PATH)),
            enable_async=True,
            autoescape=True,
        )
    return _template_env


def _background_uri() -> str:
    """背景图的 ``file://`` URI：``custom_backgrounds/`` 随机一张，空则用内置图。

    直接引用原文件，不再复制进包目录——插件装在只读位置（Docker 非 root、
    系统 site-packages）时复制会抛 PermissionError，导致每次出图都失败。
    """
    src = pick_random_user_background() or RENDER_BACKGROUNDS_PATH / "background.jpg"
    return src.resolve().as_uri() if src.is_file() else ""


async def _build_html(
    server_dict: list[dict],
    *,
    heading: str,
    hint: str,
    offline_ids: list[str],
) -> str:
    env = _get_env()
    template_name = "normal.html" if config.l4_style == "default" else "normal_old.html"
    template = env.get_template(template_name)

    return await template.render_async(
        servers=server_dict,
        max_count=config.l4_players,
        bg_url=_background_uri(),
        heading=heading,
        hint=hint,
        offline_ids=offline_ids,
    )


async def _screenshot(content: str) -> Optional[bytes]:
    """Chromium 出图；超时直接放弃，其它异常重试一次。

    异常多半是 Chromium 被 OOM 杀掉 / 断开连接，htmlrender 下一次
    ``get_browser`` 发现断开会自动重启浏览器，所以值得再试一次；超时说明
    机器本身扛不住，再等一轮只会让用户多等 ``l4_render_timeout`` 秒。
    """
    timeout = float(config.l4_render_timeout)
    for attempt in (1, 2):
        try:
            async with _render_lock:
                # ``device_scale_factor=1``：不做 2x 渲染，省 4 倍内存；JPEG 体积约为
                # PNG 的 1/3，发到 QQ 更不容易上传失败。htmlrender 0.6.7 把
                # ``wait_until="networkidle"`` 写死在 set_content 里，外部无法传。
                pic = await asyncio.wait_for(
                    html_to_pic(
                        content,
                        wait=0,
                        type="jpeg",
                        quality=90,
                        viewport={"width": 100, "height": 100},
                        template_path=f"file://{RENDER_TEMPLATES_PATH.absolute()}",
                        device_scale_factor=1,
                    ),
                    timeout=timeout,
                )
        except asyncio.TimeoutError:
            logger.warning(f"渲染服务器列表超时（>{timeout:g}s）")
            return None
        except Exception as exc:
            logger.warning(f"渲染服务器列表失败（第 {attempt} 次）: {exc!r}")
            continue
        if pic:
            return pic
        logger.warning(f"渲染服务器列表返回空字节（第 {attempt} 次）")
    return None


async def render_server_list(
    server_dict: list[dict],
    *,
    heading: str,
    hint: str = "",
    offline_ids: list[str] | None = None,
) -> Optional[bytes]:
    """Render one page of the server list as an HTML image (bytes).

    ``server_dict`` 应只包含本页要画卡片的在线条目；调用方负责过滤和分页。
    卡片上的服务器名取条目的 ``name``（缺省用 A2S 原名）。``heading`` /
    ``hint`` 是标题和标题下的小字提示。``offline_ids`` 在图片底部以文字区块
    展示（见 ``templates/normal.html``），分页时只传给最后一页。
    失败 / 超时返回 ``None``，由调用方兜底。
    """
    for server_info in server_dict:
        server = server_info["server"]
        server.player_count = server.player_count or 0
        server.max_players = server.max_players or 0
        if server_info.get("player"):
            sorted_players: list[Player] = sorted(
                server_info["player"],
                key=lambda p: p.score,
                reverse=True,
            )[: config.l4_players]
            # async 推导需先物化为列表，max() 不能直接消费 async 生成器
            durations = [
                len(str(await convert_duration(p.duration))) for p in sorted_players
            ]
            max_duration = max(durations) if durations else 1
            for p in sorted_players:
                dur = "{:^{}}".format(await convert_duration(p.duration), max_duration)
                p.name = f"{p.name} | {dur}"
            server_info["player"] = sorted_players
        else:
            server_info["player"] = []

    try:
        content = await _build_html(
            server_dict,
            heading=heading,
            hint=hint,
            offline_ids=list(offline_ids or []),
        )
    except Exception as exc:
        logger.warning(f"生成服务器列表 HTML 失败: {exc!r}")
        return None
    return await _screenshot(content)
