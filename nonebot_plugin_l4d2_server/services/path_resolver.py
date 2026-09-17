"""插件数据目录：唯一规定路径是 localstore 管理的目录。

首次启动时若 localstore 空，且下列任一旧位置有内容，``migrate_legacy()``
会复制过来：
- 插件根自带 ``data/L4D2/``（手工 / 旧版布局）
- ``localstore 子目录 services/``（v1.4.0 之前的 LOCALSTORE_SUBDIR 残留）

后续永远走 localstore 根目录。

注意：``get_plugin_data_dir()`` 用调用栈反推 ``plugin.id_``，本插件作为
``from . import services`` 子插件加载时，它会把数据写到
``<base>/<plugin>/services/``，导致组 JSON 不在根目录。所以 ``data_dir()``
直接用 localstore 的 ``BASE_DATA_DIR`` 拼 ``nonebot_plugin_l4d2_server``，
绕过 caller-plugin 解析。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from nonebot.log import logger
from nonebot_plugin_localstore import BASE_DATA_DIR

# 插件根（带 ``pyproject.toml`` 的目录），用于定位待迁移的旧数据。
_PLUGIN_ROOT = Path(__file__).parent.parent.parent

_data_dir: Path | None = None


def data_dir() -> Path:
    """唯一规定路径：``<localstore base>/nonebot_plugin_l4d2_server/``。

    直接拼 BASE_DATA_DIR，跳过 ``get_plugin_data_dir()`` 的 caller-plugin
    解析（否则被 ``services`` 子插件上下文污染到 ``services/`` 子目录）。
    """
    global _data_dir
    if _data_dir is None:
        _data_dir = BASE_DATA_DIR / "nonebot_plugin_l4d2_server"
        _data_dir.mkdir(parents=True, exist_ok=True)
    return _data_dir


def migrate_legacy() -> bool:
    """首次启动把旧位置的组 JSON 复制到 localstore。

    候选源（按优先级）：
    1. 插件根 ``data/L4D2/``（手工 / 旧版布局）
    2. localstore 子目录 ``services/``（v1.4.0 之前 LOCALSTORE_SUBDIR="l4d2"
       的残留；插件作为 ``services`` 子插件加载时 ``_get_plugin_path`` 自动
       在 ``data/nonebot_plugin_l4d2_server/`` 下加了 ``services`` 一层）。

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