"""插件数据目录：唯一规定路径是 localstore 管理的目录。

首次启动时若 localstore 空、且插件根自带 ``data/L4D2/`` 有内容，
``migrate_legacy()`` 会把后者复制过来。后续永远走 localstore。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from nonebot.log import logger
from nonebot_plugin_localstore import get_plugin_data_dir

# 插件根（带 ``pyproject.toml`` 的目录），用于定位待迁移的旧数据。
_PLUGIN_ROOT = Path(__file__).parent.parent.parent

_data_dir: Path | None = None


def data_dir() -> Path:
    """唯一规定路径：localstore 管理的插件数据目录。"""
    global _data_dir
    if _data_dir is None:
        _data_dir = get_plugin_data_dir()
        _data_dir.mkdir(parents=True, exist_ok=True)
    return _data_dir


def migrate_legacy() -> bool:
    """首次启动把插件根的 ``data/L4D2/`` 复制到 localstore。

    旧目录保留供用户手动删除。
    """
    target = data_dir()
    if any(target.iterdir()):
        return False
    legacy = _PLUGIN_ROOT / "data" / "L4D2"
    if not legacy.is_dir() or not any(legacy.iterdir()):
        return False
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