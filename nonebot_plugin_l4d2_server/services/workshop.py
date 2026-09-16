"""Steam Workshop 下载流程。

单文件 API 保留以兼容老调用方；批量 + 并发 + 流式写入新加 ``download_many``。
渲染函数（卡片）仍在 ``render/workshop.py``。
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Literal
from urllib.parse import parse_qs, urlparse

import aiofiles
from nonebot.log import logger

from ..api import WorksopInfo
from ..config import config
from ..http_helpers import stream_download, url_to_byte
from ..render.workshop import render_workshop_card
from .errors import L4Error, L4InvalidInputError
from ..services.local_server import addons_dir

ProgressCb = Callable[["WorkshopTaskResult"], Awaitable[None]]

Status = Literal["ok", "duplicate", "invalid", "download_failed"]


@dataclass
class WorkshopTaskResult:
    """批量下载的单项结果。"""

    item_id: str
    title: str | None
    status: Status
    path: Path | None = None
    error: str | None = None


def parse_workshop_id(input_str: str) -> str:
    """接受纯数字 ID 或完整 steamcommunity 链接，返回数字 ID。"""
    if input_str.isdigit():
        return input_str
    if input_str.startswith("https://steamcommunity.com/sharedfiles/filedetails"):
        params = parse_qs(urlparse(input_str).query)
        if "id" in params and params["id"][0].isdigit():
            return params["id"][0]
    raise L4InvalidInputError("无效的steam链接，请输入工坊ID或完整URL")


def parse_workshop_ids(text: str) -> list[str]:
    """从一段文本中解析出所有 workshop ID/URL。

    支持逗号、空格、换行分隔；逐项经 ``parse_workshop_id`` 校验，无效项跳过。
    """
    if not text:
        return []
    parts = re.split(r"[,\s]+", text.strip())
    ids: list[str] = []
    for raw in parts:
        raw = raw.strip()
        if not raw:
            continue
        try:
            ids.append(parse_workshop_id(raw))
        except L4InvalidInputError:
            continue
    # 去重保序
    seen: set[str] = set()
    deduped: list[str] = []
    for one in ids:
        if one not in seen:
            seen.add(one)
            deduped.append(one)
    return deduped


async def fetch_info(workshop_input: str) -> WorksopInfo:
    """解析输入 → 渲染卡片 → 返回原始 info dict。"""
    workshop_id = parse_workshop_id(workshop_input)
    return await render_workshop_card(workshop_id)


def _target_path(server_index: int, info: WorksopInfo) -> Path:
    addons = addons_dir(server_index) or (config.data_dir / "addons")
    addons.mkdir(parents=True, exist_ok=True)
    return addons / info["filename"]


async def _download_one(
    item_id: str,
    server_index: int,
    sem: asyncio.Semaphore,
    on_progress: ProgressCb | None,
) -> WorkshopTaskResult:
    async with sem:
        try:
            info = await fetch_info(item_id)
        except L4InvalidInputError as exc:
            return WorkshopTaskResult(item_id, None, "invalid", error=str(exc))
        except L4Error as exc:
            return WorkshopTaskResult(item_id, None, "download_failed", error=str(exc))
        except Exception as exc:  # 网络异常等
            return WorkshopTaskResult(
                item_id, None, "download_failed", error=str(exc),
            )

        target = _target_path(server_index, info)
        if target.is_file():
            result = WorkshopTaskResult(
                item_id, info["title"], "duplicate", path=target,
            )
            if on_progress is not None:
                await on_progress(result)
            return result

        try:
            await stream_download(info["file_url"], target)
        except Exception as exc:
            logger.warning(f"工坊下载失败 [{item_id}]: {exc}")
            result = WorkshopTaskResult(
                item_id, info["title"], "download_failed", error=str(exc),
            )
        else:
            result = WorkshopTaskResult(
                item_id, info["title"], "ok", path=target,
            )

        if on_progress is not None:
            await on_progress(result)
        return result


async def download_many(
    ids_or_urls: list[str],
    server_index: int,
    *,
    on_progress: ProgressCb | None = None,
) -> list[WorkshopTaskResult]:
    """并发下载多个创意工坊条目。

    并发上限 ``config.l4_workshop_concurrency``（默认 3，上限 8），
    避免 Steam CDN 同时被打穿。每项通过 ``on_progress`` 回调可发送逐项进度。
    """
    if not ids_or_urls:
        return []
    sem = asyncio.Semaphore(max(1, int(config.l4_workshop_concurrency)))
    return await asyncio.gather(
        *[_download_one(one, server_index, sem, on_progress) for one in ids_or_urls],
    )


async def download_to_addons(info: WorksopInfo, server_index: int) -> Path | None:
    """兼容老调用方的单文件下载入口。

    推荐走 ``download_many``；本函数继续用 ``url_to_byte`` 是为了不破坏
    已有调用方（如 ``commands/local.py`` 之外的脚本）。
    """
    # 懒加载 alconna：避免被 ``services/__init__.py`` 提前 import 触发
    # ``nonebot_plugin_alconna`` 走普通 importlib 进 sys.modules，导致后续
    # ``require("nonebot_plugin_alconna")`` 无法给模块设置 ``__plugin__``。
    from nonebot_plugin_alconna import UniMessage

    target = _target_path(server_index, info)
    if target.is_file():
        logger.info(f"地图文件已存在: {target}")
        await UniMessage.text(f"地图已存在: {info['filename']}").finish()
        return None

    data = await url_to_byte(info["file_url"])
    if data is None:
        logger.error(f"下载失败: {info['file_url']}")
        await UniMessage.text("下载失败").finish()
        return None

    async with aiofiles.open(target, "wb") as f:
        await f.write(data)

    logger.info(f"地图下载完成: {target}")
    await UniMessage.text(f"✅ 地图下载完成: {info['filename']}").send()
    await UniMessage.file(path=target, name=f"{info['title']}.vpk").send()
    return target
