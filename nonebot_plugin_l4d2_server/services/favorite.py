"""收藏 / 订阅服务。

每个收藏绑定到一个具体的目标群（``target_group_id``），由 ``run_favorite_check``
周期检查对应的服务器，状态变化时按群推送。同一个 ``host:port`` 即使被多个群
收藏，也只会做一次 A2S 查询，结果按群分发，避免重复打扰。

存储：

- ``favorites.json`` — ``[{"tag", "server_id", "host", "port",
  "target_group_id", "server_name_snapshot", "created_at"}]``
- ``notify_state.json`` — ``{"host:port": {"online", "player_count",
  "last_check_at", "last_alert_at"}}``

调度：``init_favorite_scheduler`` 在 ``_on_startup`` 注册一个 interval 任务，
周期 = ``config.l4_favorite_check_interval``。scheduler 由
``nonebot-plugin-apscheduler`` 提供。
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import aiofiles
import ujson as json
from nonebot import get_bot
from nonebot.log import logger

from ..api import L4API
from ..config import config
from ..consts import FAVORITES_FILENAME, NOTIFY_STATE_FILENAME
from ..registry import registry
from .errors import L4NotFoundError

# 同一进程内的写锁，避免 scheduler 和用户命令同时改文件
_write_lock = asyncio.Lock()

_STATE_DEFAULT: dict[str, Any] = {
    "online": False,
    "player_count": 0,
    "last_check_at": 0,
    "last_alert_at": 0,
}


# ---------------- 存储路径 ----------------

def _favorites_path() -> Path:
    return config.data_dir / FAVORITES_FILENAME


def _state_path() -> Path:
    return config.data_dir / NOTIFY_STATE_FILENAME


async def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ---------------- favorites.json ----------------

async def _load_favorites() -> list[dict]:
    await _ensure_parent(_favorites_path())
    p = _favorites_path()
    if not p.is_file():
        return []
    async with aiofiles.open(p, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "[]")
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.warning(f"[l4] 解析 favorites.json 失败: {exc}")
        return []


async def _save_favorites(items: list[dict]) -> None:
    await _ensure_parent(_favorites_path())
    async with aiofiles.open(_favorites_path(), "w", encoding="utf-8") as f:
        await f.write(json.dumps(items, ensure_ascii=False, indent=4) + "\n")


# ---------------- notify_state.json ----------------

async def _load_state() -> dict[str, dict]:
    await _ensure_parent(_state_path())
    p = _state_path()
    if not p.is_file():
        return {}
    async with aiofiles.open(p, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "{}")
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning(f"[l4] 解析 notify_state.json 失败: {exc}")
        return {}


async def _save_state(state: dict[str, dict]) -> None:
    await _ensure_parent(_state_path())
    async with aiofiles.open(_state_path(), "w", encoding="utf-8") as f:
        await f.write(json.dumps(state, ensure_ascii=False, indent=4) + "\n")


# ---------------- 公开接口 ----------------

async def add_favorite(
    tag: str,
    server_id: int | str,
    target_group_id: int,
) -> dict:
    """收藏 ``tag`` 下 id 为 ``server_id`` 的服务器到目标群。

    重复收藏同一服务器到同一群：返回已存在的条目，不重复添加。
    """
    entry = registry.get_server(tag, server_id)
    if entry is None:
        raise L4NotFoundError(f"未在组「{tag}」中找到服务器 {server_id}")

    host = str(entry.get("host") or "")
    port = int(entry.get("port") or 0)
    if not host or not port:
        raise L4NotFoundError(f"组「{tag}」服务器 {server_id} 的 host/port 缺失")

    async with _write_lock:
        items = await _load_favorites()
        for it in items:
            if (
                it.get("tag") == tag
                and str(it.get("server_id")) == str(entry.get("id"))
                and int(it.get("target_group_id", 0)) == int(target_group_id)
            ):
                return it
        new_item = {
            "tag": tag,
            "server_id": str(entry.get("id")),
            "host": host,
            "port": port,
            "target_group_id": int(target_group_id),
            "server_name_snapshot": str(entry.get("ip") or f"{host}:{port}"),
            "created_at": int(time.time()),
        }
        items.append(new_item)
        await _save_favorites(items)
        return new_item


async def remove_favorite(
    tag: str,
    server_id: int | str,
    target_group_id: int,
) -> bool:
    """取消当前群对 ``tag`` 下某服务器的收藏。

    仅删除当前群对应的条目；其他群的订阅不受影响。
    """
    async with _write_lock:
        items = await _load_favorites()
        new_items = [
            it
            for it in items
            if not (
                it.get("tag") == tag
                and str(it.get("server_id")) == str(server_id)
                and int(it.get("target_group_id", 0)) == int(target_group_id)
            )
        ]
        if len(new_items) == len(items):
            return False
        await _save_favorites(new_items)
        return True


async def list_favorites(target_group_id: int | None = None) -> list[dict]:
    """列出收藏。``target_group_id=None`` 时返回所有群的收藏。"""
    items = await _load_favorites()
    if target_group_id is None:
        return items
    return [it for it in items if int(it.get("target_group_id", 0)) == int(target_group_id)]


async def update_notify_target(
    tag: str,
    server_id: int | str,
    new_group_id: int,
) -> bool:
    """把收藏的推送目标改成新群号。仅匹配一条最早记录；其他群订阅保持不动。"""
    async with _write_lock:
        items = await _load_favorites()
        matched = False
        for it in items:
            if (
                not matched
                and it.get("tag") == tag
                and str(it.get("server_id")) == str(server_id)
            ):
                it["target_group_id"] = int(new_group_id)
                matched = True
        if not matched:
            return False
        await _save_favorites(items)
        return True


# ---------------- 巡检 + 推送 ----------------

def _is_empty_player_signal(server: Any) -> bool:
    """服务器可达但 sentinel（无响应）状态。"""
    name = getattr(server, "server_name", "")
    return name == "服务器无响应"


def _format_alert(
    item: dict,
    *,
    prev_online: bool,
    prev_player_count: int,
    now_online: bool,
    now_player_count: int,
) -> str | None:
    """根据状态变化生成推送文案；不需要推则返回 None。"""
    name = item.get("server_name_snapshot") or f"{item.get('host')}:{item.get('port')}"
    tag = item.get("tag")
    sid = item.get("server_id")
    delta = abs(now_player_count - prev_player_count)
    threshold = int(config.l4_favorite_player_delta)

    if not prev_online and now_online:
        return f"🟢 {tag}{sid} {name} 已上线（{now_player_count} 人）"
    if prev_online and not now_online:
        return f"🔴 {tag}{sid} {name} 已离线"
    if prev_online and now_online and delta >= threshold:
        direction = "↗" if now_player_count > prev_player_count else "↘"
        return (
            f"{direction} {tag}{sid} {name} 人数变化 "
            f"{prev_player_count} → {now_player_count}"
        )
    return None


async def _send_to_group(group_id: int, text: str, bot: Any) -> None:
    """向指定群发文本。失败只记 ERROR，不抛。"""
    try:
        from nonebot.adapters.onebot.v11 import Message  # 局部导入
        await bot.send_group_msg(group_id=int(group_id), message=Message(text))
    except Exception as exc:
        logger.error(f"[l4] 推送失败 group={group_id}: {exc}")


async def run_favorite_check(bot: Any | None = None) -> None:
    """scheduler 周期调用：去重 A2S 查服，按状态变化推送到对应群。

    使用 ``a2s_info_batch_ordered`` 拿保序结果，避免按 steam_id 排序后无法
    对齐 host:port；want_players=False（订阅只关心 online / player_count）。
    """
    items = await _load_favorites()
    if not items:
        return

    if bot is None:
        try:
            bot = get_bot()
        except Exception:
            logger.debug("[l4] 收藏巡检：bot 还未连接，跳过本轮")
            return

    # 按 host:port 去重，保序以匹配 a2s_info_batch_ordered 的返回
    deduped: list[tuple[str, int]] = []
    seen: set[str] = set()
    for it in items:
        key = f"{it['host']}:{it['port']}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append((str(it["host"]), int(it["port"])))

    ordered = await L4API.a2s_info_batch_ordered(deduped, want_players=False)
    now_ts = int(time.time())
    state_map: dict[str, dict[str, Any]] = {}
    for (host, port, server, _players) in ordered:
        online = not _is_empty_player_signal(server)
        state_map[f"{host}:{port}"] = {
            "online": online,
            "player_count": int(getattr(server, "player_count", 0) or 0),
            "last_check_at": now_ts,
        }

    state = await _load_state()
    by_group: dict[int, list[str]] = {}
    for it in items:
        key = f"{it['host']}:{it['port']}"
        now = state_map.get(key, {"online": False, "player_count": 0})
        prev = state.get(key, _STATE_DEFAULT.copy())

        # 30 分钟内同类事件不重复推送（避免上下线抖动刷屏）
        prev_online = bool(prev.get("online"))
        now_online = bool(now["online"])
        if (
            (prev_online != now_online)
            and now_ts - int(prev.get("last_alert_at", 0)) < 1800
        ):
            continue

        line = _format_alert(
            it,
            prev_online=prev_online,
            prev_player_count=int(prev.get("player_count", 0)),
            now_online=now_online,
            now_player_count=int(now["player_count"]),
        )
        if line is None:
            continue

        # 更新 last_alert_at：仅在 online 翻转或人数变化 ≥ 阈值时
        if prev_online != now_online or abs(
            int(prev.get("player_count", 0)) - int(now["player_count"]),
        ) >= int(config.l4_favorite_player_delta):
            prev["last_alert_at"] = now_ts
        prev["online"] = now_online
        prev["player_count"] = int(now["player_count"])
        prev["last_check_at"] = now_ts
        state[key] = prev

        gid = int(it["target_group_id"])
        by_group.setdefault(gid, []).append(line)

    await _save_state(state)

    if not by_group:
        return
    for gid, lines in by_group.items():
        await _send_to_group(gid, "\n".join(lines), bot)


# ---------------- scheduler 接入 ----------------

async def _scheduled_check() -> None:
    await run_favorite_check()


async def init_favorite_scheduler() -> None:
    """注册 apscheduler 定时任务；启动期调一次，幂等。"""
    try:
        from nonebot_plugin_apscheduler import scheduler
    except Exception as exc:
        logger.warning(f"[l4] apscheduler 未安装，收藏巡检不会自动运行: {exc}")
        return
    interval = max(30, int(config.l4_favorite_check_interval))
    scheduler.add_job(
        _scheduled_check,
        "interval",
        seconds=interval,
        id="l4_favorite_check",
        replace_existing=True,
        next_run_time=None,  # 启动后第一轮不立即触发，避免和 on_startup 抢资源
    )
    logger.success(f"[l4] 收藏巡检已注册：每 {interval} 秒")
