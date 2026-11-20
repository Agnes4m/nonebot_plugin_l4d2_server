"""让 litehtml / fontconfig 在任意平台都能拿到可用的字体配置。

htmlkit 的 ``init_fontconfig()`` 挂在 ``driver.on_startup`` 上，它只会在
``FcConfig.fontconfig_file`` 有值时才把 ``FONTCONFIG_FILE`` 写进环境变量；
该值为空时它**不动**环境变量。所以本插件可以在 import 阶段（早于 startup）
先把自己包内那份 ``render/fonts/fonts.conf`` 指过去，Windows / Linux 都不用
再在 ``.env`` 里配绝对路径。

用户显式配置的 ``FONTCONFIG_FILE`` 优先级更高：htmlkit 在 startup 时会把
``os.environ`` 覆盖回它的值。
"""

from __future__ import annotations

import os
from pathlib import Path

from nonebot.log import logger

# 包内路径：随 pyproject 的 ``render/fonts/*`` package-data 一起发布
FONTCONFIG_PATH = Path(__file__).parent / "render" / "fonts" / "fonts.conf"


def ensure_fontconfig_env() -> None:
    """在没有 ``FONTCONFIG_FILE`` 时指向包内 fonts.conf。"""
    existing = os.environ.get("FONTCONFIG_FILE")
    if existing:
        logger.debug(f"[l4] 沿用已配置的 FONTCONFIG_FILE: {existing}")
        return

    if not FONTCONFIG_PATH.is_file():
        logger.warning(
            f"[l4] 找不到内置 fonts.conf，出图字体可能不一致: {FONTCONFIG_PATH}",
        )
        return

    # fontconfig 在 Windows 上也吃正斜杠；as_posix() 让两个平台用同一份写法
    os.environ["FONTCONFIG_FILE"] = FONTCONFIG_PATH.as_posix()
    logger.debug(f"[l4] 使用内置 FONTCONFIG_FILE: {FONTCONFIG_PATH.as_posix()}")
