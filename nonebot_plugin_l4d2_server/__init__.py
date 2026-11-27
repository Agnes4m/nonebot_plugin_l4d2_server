"""
* Copyright (c) 2023, Agnes Digital
*
* This program is free software: you can redistribute it and or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import time

from nonebot import get_driver, require
from nonebot.log import logger
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

# 依赖插件声明 必须在导入其它插件模块之前执行。
# htmlkit 走 litehtml 本地渲染，不需要 Chromium，也不依赖 localstore。
# fontconfig 必须在 htmlkit 的 driver.on_startup 之前指好：缺 fonts.conf 时
# sans-serif 这类通用字族没有映射，中英数字会拆成几套字形（详见 docs/bug.md）。
from .fontconfig_env import ensure_fontconfig_env  # noqa: E402

ensure_fontconfig_env()

require("nonebot_plugin_alconna")
require("nonebot_plugin_htmlkit")
require("nonebot_plugin_apscheduler")

from . import commands  # noqa: E402, F401  (registers all commands)
from .config import ConfigModel  # noqa: E402
from .services import migrate, sourceban  # noqa: E402
from .version import __version__  # noqa: E402

driver = get_driver()

# Initial scan to populate command aliases before any rule refresh.
from .registry import registry as _registry  # noqa: E402

_registry.scan_commands()


@driver.on_startup
async def _on_startup() -> None:
    from .commands.admin import register_picker_handlers
    from .commands.query import refresh_server_command_rule
    from .config import config
    from .render.background import ensure_user_background_dir
    from .services.blocklist import ensure_user_words_dir
    from .services.favorite import init_favorite_scheduler
    from .services.history import purge_older_than
    from .services.path_resolver import migrate_legacy

    config.data_dir.mkdir(parents=True, exist_ok=True)  # 确保数据目录存在
    migrate_legacy()  # 首次启动把插件根 data/L4D2/ 复制过去
    migrate.migrate_legacy_layout()
    await sourceban.reload_registry()
    sourceban.register_anne_alias()
    refresh_server_command_rule()
    register_picker_handlers()
    ensure_user_background_dir()
    ensure_user_words_dir()
    await init_favorite_scheduler()
    # 启动后台 A2S 历史记录任务 + 清过期记录
    await _start_history_recorder()
    _start_history_hot_job()
    await asyncio.to_thread(
        purge_older_than,
        int(config.l4_history_retention_days),
    )
    _start_history_purge_job()


def _start_history_purge_job() -> None:
    """每天凌晨 4 点清一次过期历史。

    只在启动时清一次是不够的：bot 连续跑几个月不重启，``a2s_history`` 会一直
    涨（每 ``l4_history_interval`` 秒 × 每台服一条）。
    """
    from nonebot_plugin_apscheduler import scheduler

    from .config import config
    from .services.history import purge_older_than

    def _purge() -> None:
        try:
            removed = purge_older_than(int(config.l4_history_retention_days))
        except Exception as exc:
            logger.warning(f"[l4] 清理过期历史失败: {exc}")
            return
        if removed:
            logger.info(f"[l4] 清理过期历史记录 {removed} 条")

    try:
        scheduler.add_job(
            _purge,
            "cron",
            hour=4,
            minute=0,
            id="l4_history_purge",
            replace_existing=True,
        )
    except Exception as exc:
        logger.warning(f"[l4] 注册历史清理任务失败: {exc}")


async def _start_history_recorder() -> None:
    """apscheduler 注册 interval 任务，周期 ``config.l4_history_interval`` 秒。

    任务对 ``registry.group_names`` 内每个组的每台服跑一次 ``record``。
    收藏巡检的 ``run_favorite_check`` 已经会写历史，本任务只覆盖**未被收藏**
    的服，避免「你只查不收藏的服没历史」。

    周期为 0 表示不注册：插件不再自己发 A2S 请求，只有收到查服指令时才查。

    离线服按指数退避跳过（``l4_history_dead_retry_max``）：实测 103 台里
    48 台从来没开过，每轮都查等于每 5 分钟白等 13 秒（占位全天的 1.27 小时）。
    这里**不走** A2S 的 probe 快扫 —— recorder 与整组查询分属两套信号量，
    用 probe 会跟用户的 /云 抢同一个 Semaphore(16)，实测把 /云 从 2.2 秒拖到 8.4 秒。
    """
    from nonebot_plugin_apscheduler import scheduler

    from .config import config
    from .services.history import record

    interval = int(config.l4_history_interval)
    if interval <= 0:
        logger.info(
            "[l4] 历史记录巡检已关闭（l4_history_interval=0），仅在查服指令时请求",
        )
        return

    # 每台服的失败次数 -> 下次允许重试的时刻（monotonic 秒）
    _dead_streak: dict[tuple[str, int], int] = {}
    _retry_at: dict[tuple[str, int], float] = {}
    backoff_cap = int(getattr(config, "l4_history_dead_retry_max", 7200))

    def _next_retry_delay(streak: int) -> int:
        """5 分钟起步翻倍，封顶 ``backoff_cap``。streak=1 → interval。"""
        delay = interval * (2 ** max(0, streak - 1))
        return min(max(interval, delay), backoff_cap)

    async def _record_all() -> None:
        from .api import L4API
        from .registry import registry

        ips: list[tuple[str, int]] = []
        for tag in registry.group_names:
            for entry in registry.get(tag) or []:
                ips.append((entry["host"], int(entry["port"])))
        if not ips:
            return

        now = time.monotonic()
        # 退避窗口内的死服直接跳过；backoff_cap=0 时永不过滤（旧行为）。
        # 首次运行没有退避记录，会完整查一遍 103 台（约 17 秒），这样新加的服
        # 能在第一轮就被发现；之后死服退避，稳定在 55 台 2.6 秒。
        pending: list[tuple[str, int]] = []
        for ip in ips:
            if backoff_cap > 0 and _retry_at.get(ip, 0.0) > now:
                continue
            pending.append(ip)
        skipped = len(ips) - len(pending)
        if not pending:
            logger.debug(f"[l4] 历史巡检：{len(ips)} 台都在退避窗口内，本轮跳过")
            return

        try:
            results = await L4API.a2s_info_batch(pending, want_players=False)
        except Exception as exc:
            logger.warning(f"[l4] 历史记录批量失败: {exc}")
            return

        dead = 0
        for (server, _), ip in zip(results, pending):
            record(
                host=ip[0],
                port=ip[1],
                server_name=str(getattr(server, "server_name", "") or ""),
                map_name=str(getattr(server, "map_name", "") or ""),
                player_count=int(getattr(server, "player_count", 0) or 0),
                max_players=int(getattr(server, "max_players", 0) or 0),
                ping=int(getattr(server, "ping", 0) or 0) or None,
            )
            # max_players == 0 是离线哨兵；连续离线就退避，直到上限
            if backoff_cap > 0 and int(getattr(server, "max_players", 0) or 0) == 0:
                dead += 1
                streak = _dead_streak.get(ip, 0) + 1
                _dead_streak[ip] = streak
                _retry_at[ip] = time.monotonic() + _next_retry_delay(streak)
            else:
                _dead_streak.pop(ip, None)
                _retry_at.pop(ip, None)

        logger.debug(
            f"[l4] 历史巡检：记录 {len(pending)} 台（离线 {dead}，退避跳过 {skipped}），"
            f"退避中 {len(_retry_at)} 台",
        )

    try:
        scheduler.add_job(
            _record_all,
            "interval",
            seconds=interval,
            id="l4_history_record",
            replace_existing=True,
        )
    except Exception as exc:
        logger.warning(f"[l4] 注册历史记录任务失败: {exc}")


def _start_history_hot_job() -> None:
    """「热服」加密采样：只对最近确实有人的服按短周期补采样。

    背景：整组巡检周期是 1 小时（``l4_history_interval``），热力图的一个格子
    就只有每小时 1 个样本，凑不到 ``heatmap`` 要求的「>=3 个样本」下限，图上
    永远是空的。但把整组周期调回 5 分钟又会让 48 台永久离线的服把每轮拖慢
    十几秒。

    折中：主巡检保持 1 小时管全部服；本任务每 ``l4_history_hot_interval`` 秒
    只挑 ``l4_history_hot_window`` 内出现过玩家的服（实测通常个位数到二十几
    台，单轮 0.1-0.5 秒）补一次采样。没人玩的服自然掉出热服名单，采样成本
    跟着热度走。

    与主巡检一致**不走 probe**：probe 用 ``_probe_sem``，会跟用户的 ``/云``
    抢并发槽位。实现在 ``services/history_hot.py``。
    """
    from nonebot_plugin_apscheduler import scheduler

    from .config import config
    from .services.history_hot import register_hot_job

    register_hot_job(scheduler, config)


__plugin_meta__ = PluginMetadata(
    name="求生之路小助手",
    description="可用于管理求生之路查服和本地管理",
    usage="群内对有关求生之路的查询和操作",
    config=ConfigModel,
    type="application",
    homepage="https://github.com/Agnes4m/nonebot_plugin_l4d2_server",
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "version": __version__,
        "author": "Agnes4m <Z735803792@163.com>",
    },
)
