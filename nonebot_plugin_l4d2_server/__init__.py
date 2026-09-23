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

from nonebot import get_driver, require
from nonebot.log import logger
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

# 依赖插件声明 必须在导入其它插件模块之前执行。
# htmlrender 0.6.x 的 ``__init__.py`` 会 ``require("nonebot_plugin_localstore")``，
# 所以 localstore 会通过 htmlrender 间接加载；如果想收藏巡检 / 定时任务立刻可用，
# 把 apscheduler 也显式 require 一下。
require("nonebot_plugin_alconna")
require("nonebot_plugin_htmlrender")
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
    await init_favorite_scheduler()
    # 启动后台 A2S 历史记录任务 + 清过期记录
    await _start_history_recorder()
    await asyncio.to_thread(
        purge_older_than,
        int(config.l4_history_retention_days),
    )


async def _start_history_recorder() -> None:
    """apscheduler 注册 interval 任务，周期 ``config.l4_history_interval`` 秒。

    任务对 ``registry.group_names`` 内每个组的每台服跑一次 ``record``。
    收藏巡检的 ``run_favorite_check`` 已经会写历史，本任务只覆盖**未被收藏**
    的服，避免「你只查不收藏的服没历史」。
    """
    from nonebot_plugin_apscheduler import scheduler

    from .config import config
    from .services.history import record

    async def _record_all() -> None:
        from .api import L4API
        from .registry import registry

        ips: list[tuple[str, int]] = []
        for tag in registry.group_names:
            for entry in registry.get(tag) or []:
                ips.append((entry["host"], int(entry["port"])))
        if not ips:
            return
        try:
            results = await L4API.a2s_info_batch(ips, want_players=False)
        except Exception as exc:
            logger.warning(f"[l4] 历史记录批量失败: {exc}")
            return
        for (server, _), ip in zip(results, ips):
            record(
                host=ip[0],
                port=ip[1],
                server_name=str(getattr(server, "server_name", "") or ""),
                map_name=str(getattr(server, "map_name", "") or ""),
                player_count=int(getattr(server, "player_count", 0) or 0),
                max_players=int(getattr(server, "max_players", 0) or 0),
                ping=int(getattr(server, "ping", 0) or 0) or None,
            )

    try:
        scheduler.add_job(
            _record_all,
            "interval",
            seconds=int(config.l4_history_interval),
            id="l4_history_record",
            replace_existing=True,
        )
    except Exception as exc:
        logger.warning(f"[l4] 注册历史记录任务失败: {exc}")


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
