"""历史巡检的「热服加密采样」任务。

背景：整组巡检周期是 1 小时（``l4_history_interval``），热力图一个格子只有
每小时 1 个样本，凑不到 ``heatmap`` 要求的「>=3 个样本」下限，图上永远是空
的。但把整组周期调回 5 分钟又会让几十台永久离线的服把每轮拖慢十几秒。

折中方案（本模块）：主巡检保持 1 小时管全部服；这里再挂一个短周期任务，只挑
「最近确实有人」的服补采样 —— 没人玩的服自然掉出热服名单，采样成本跟着热度
走。实测热服通常个位数到二十几台，单轮 0.1-0.5 秒。

和主巡检一致**不走 A2S 的 probe 快扫**：probe 用 ``_probe_sem``，会跟用户的
``/云`` 抢同一个 Semaphore(16)，实测把 ``/云`` 从 2.2 秒拖到 8.4 秒。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nonebot.log import logger

if TYPE_CHECKING:  # pragma: no cover
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from ..config import ConfigModel

HOT_JOB_ID = "l4_history_hot"


def hot_job_settings(cfg: "ConfigModel") -> tuple[int, int] | None:
    """读配置决定要不要开加密采样；返回 ``(周期, 窗口)`` 或 None。"""
    interval = int(getattr(cfg, "l4_history_hot_interval", 0) or 0)
    window = int(getattr(cfg, "l4_history_hot_window", 0) or 0)
    if interval <= 0 or window <= 0:
        return None
    return interval, window


async def record_hot_servers(window: int) -> int:
    """对 ``window`` 秒内有人的服补一次采样，返回采样台数。"""
    from ..api import L4API
    from ..registry import registry
    from .history import recent_active_hosts, record

    known = {
        (entry["host"], int(entry["port"]))
        for tag in registry.group_names
        for entry in registry.get(tag) or []
    }
    hot = [ip for ip in recent_active_hosts(window) if ip in known]
    if not hot:
        return 0
    try:
        results = await L4API.a2s_info_batch(hot, want_players=False)
    except Exception as exc:  # noqa: BLE001 - 后台任务不能往外抛
        logger.warning(f"[l4] 热服采样批量失败: {exc}")
        return 0
    for (server, _), ip in zip(results, hot):
        record(
            host=ip[0],
            port=ip[1],
            server_name=str(getattr(server, "server_name", "") or ""),
            map_name=str(getattr(server, "map_name", "") or ""),
            player_count=int(getattr(server, "player_count", 0) or 0),
            max_players=int(getattr(server, "max_players", 0) or 0),
            ping=int(getattr(server, "ping", 0) or 0) or None,
        )
    logger.debug(f"[l4] 热服采样：{len(hot)} 台")
    return len(hot)


def register_hot_job(scheduler: "AsyncIOScheduler", cfg: "ConfigModel") -> bool:
    """按配置把加密采样任务挂到 scheduler；返回是否注册成功。"""
    settings = hot_job_settings(cfg)
    if settings is None:
        logger.info(
            "[l4] 热服加密采样已关闭（L4_HISTORY_HOT_INTERVAL 或 "
            "L4_HISTORY_HOT_WINDOW 为 0）",
        )
        return False
    interval, window = settings

    async def _job() -> None:
        await record_hot_servers(window)

    try:
        scheduler.add_job(
            _job,
            "interval",
            seconds=interval,
            id=HOT_JOB_ID,
            replace_existing=True,
        )
    except Exception as exc:  # noqa: BLE001 - 注册失败只告警，不影响插件
        logger.warning(f"[l4] 注册热服采样任务失败: {exc}")
        return False
    logger.success(
        f"[l4] 热服加密采样已注册：每 {interval} 秒，对象为 {window} 秒内有人的服",
    )
    return True


__all__: list[Any] = [
    "HOT_JOB_ID",
    "hot_job_settings",
    "record_hot_servers",
    "register_hot_job",
]
