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

from nonebot import get_driver, require
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
    from .services.path_resolver import migrate_legacy_to_localstore

    # v1.4.0：先确定 data 根（localstore or legacy），再做一次性迁移。
    migrate_legacy_to_localstore()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    migrate.migrate_legacy_layout()
    # 只从磁盘 JSON 加载，避免每次启动都重新抓取所有 SourceBans 页面；
    # 需要更新缓存时使用 l4刷新组 命令。
    await sourceban.reload_registry()
    sourceban.register_anne_alias()
    refresh_server_command_rule()
    register_picker_handlers()  # tj / zl / kl（必须等 registry.commands 填好）
    ensure_user_background_dir()
    await init_favorite_scheduler()


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