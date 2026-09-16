"""数据目录解析：localstore 模式 vs 旧 l4_path 模式。

仅一个权威入口 ``resolve_data_dir()``；所有依赖 ``config.data_dir`` 的
代码都通过该 property 拿到当前生效的根目录，不再自己 ``Path(config.l4_path)``。

localstore 模式下还提供 ``migrate_legacy_to_localstore()``：在目标目录为空
且旧 ``data/L4D2`` 仍有内容时，一次性复制过去，保留旧目录供用户确认后手动删除。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from nonebot.log import logger

from ..config import config
from ..consts import DEFAULT_DATA_DIR


def resolve_data_dir() -> Path:
    """运行时权威的数据根目录。

    ``config.l4_use_localstore=True`` 时返回
    ``<localstore 根>/nonebot_plugin_l4d2_server/<l4_localstore_subdir>``；
    关闭时退回 ``Path(config.l4_path)``。
    """
    if config.l4_use_localstore:
        # 关键：``nonebot_plugin_localstore`` 必须等到 ``require`` 走完作为插件
        # 加载好之后再 import；否则会被普通 importlib 提前塞进 sys.modules，
        # 后续 PluginLoader 跳过 exec_module，``__plugin__`` 永远是 None。
        from nonebot_plugin_localstore import get_plugin_data_dir

        target = get_plugin_data_dir() / config.l4_localstore_subdir
        target.mkdir(parents=True, exist_ok=True)
        return target
    return Path(config.l4_path)


def migrate_legacy_to_localstore() -> bool:
    """首次开启 localstore 时把旧 ``data/L4D2`` 内容复制到新目录。

    仅当新目录为空、且旧目录存在且非空时执行；旧目录会保留以便用户手动确认后删除。
    返回是否实际迁移了内容。
    """
    if not config.l4_use_localstore:
        return False
    target = resolve_data_dir()
    if target.exists() and any(target.iterdir()):
        return False
    legacy = Path(DEFAULT_DATA_DIR)
    if not legacy.exists() or not any(legacy.iterdir()):
        return False
    target.mkdir(parents=True, exist_ok=True)
    logger.info(f"[l4] 迁移 {legacy} → {target}")
    moved = 0
    for item in legacy.iterdir():
        dest = target / item.name
        try:
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        except OSError as exc:
            logger.warning(f"[l4] 迁移 {item} 失败: {exc}")
            continue
        moved += 1
    logger.success(f"[l4] 迁移完成：共 {moved} 项；旧目录 {legacy} 已保留，可手动删除")
    return moved > 0
