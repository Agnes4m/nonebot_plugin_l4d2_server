"""插件数据目录：唯一规定路径是 ``<cwd>/data/nonebot_plugin_l4d2_server/``。

不管 ``localstore_use_cwd`` 设的是什么（True/False），都走 cwd-based 路径。
``get_plugin_data_dir()`` 用调用栈反推 ``plugin.id_``，本插件作为
``from . import services`` 子插件加载时，它会把数据写到
``<base>/<plugin>/services/``，并且 ``BASE_DATA_DIR`` 在
``localstore_use_cwd=False`` 时退回到 ``user_data_dir("nonebot2")``
= ``~/.local/share/nonebot2/``，跟用户预期的 cwd-relative 路径不一致。

所以本插件**直接拼 ``Path.cwd() / "data"``**，不依赖 localstore 的解析逻辑。

首次启动时若目标目录空、且下列任一旧位置有内容，``migrate_legacy()``
会复制过来：
- 插件根自带 ``data/L4D2/``（手工 / 旧版布局）
- ``<cwd>/data/nonebot_plugin_l4d2_server/services/``（v1.4.0 之前
  LOCALSTORE_SUBDIR 残留路径）
- ``<cwd>/data/``（``localstore_use_cwd=False`` 时的旧 localstore
  路径 ``data/nonebot_plugin_l4d2_server/`` —— 注意是 user_data_dir
  之外的 cwd 位置，跟本插件现在用的位置同名；要靠 cwd 才能匹配）
"""

from __future__ import annotations

import shutil
from pathlib import Path

from nonebot.log import logger

# 插件根（带 ``pyproject.toml`` 的目录），用于定位待迁移的旧数据。
_PLUGIN_ROOT = Path(__file__).parent.parent.parent

_data_dir: Path | None = None


def data_dir() -> Path:
    """唯一规定路径：``<cwd>/data/nonebot_plugin_l4d2_server/``。

    不用 ``nonebot_plugin_localstore.BASE_DATA_DIR`` / ``get_plugin_data_dir()``：
    那个会被 ``localstore_use_cwd`` 切到 ``~/.local/share/nonebot2/``，
    也会被 caller-plugin 解析污染到 ``services/`` 子目录。
    """
    global _data_dir
    if _data_dir is None:
        _data_dir = Path.cwd() / "data" / "nonebot_plugin_l4d2_server"
        _data_dir.mkdir(parents=True, exist_ok=True)
    return _data_dir


def migrate_legacy() -> bool:
    """首次启动把旧位置的组 JSON 复制到 cwd-based 目标。

    候选源（按优先级）：
    1. 插件根 ``data/L4D2/``（手工 / 旧版布局）
    2. ``<cwd>/data/nonebot_plugin_l4d2_server/services/``
       （v1.4.0 之前 LOCALSTORE_SUBDIR="l4d2" 残留路径，caller-plugin
       解析污染到 services/ 子目录）

    旧位置保留供用户手动确认后删除。
    """
    target = data_dir()
    if any(target.iterdir()):
        return False

    candidates = [
        _PLUGIN_ROOT / "data" / "L4D2",
        target / "services",  # v1.4.0 之前 LOCALSTORE_SUBDIR 残留
    ]
    for legacy in candidates:
        if not legacy.is_dir() or not any(legacy.iterdir()):
            continue
        moved = 0
        for item in legacy.iterdir():
            dest = target / item.name
            try:
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
                moved += 1
            except OSError as exc:
                logger.warning(f"[l4] 迁移 {item} 失败: {exc}")
        logger.success(f"[l4] 迁移 {moved} 项：{legacy} → {target}")
        return moved > 0
    return False
