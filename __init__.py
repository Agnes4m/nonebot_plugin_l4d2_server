"""目录加载入口（仅在插件以源码目录形式被加载时使用）。

插件通过 pip 安装后由 nonebot 直接导入内层包；此时本文件不应再触发
嵌套 load_plugins，否则同一插件会被初始化两次。
"""

import sys
from pathlib import Path

from nonebot import load_plugins

if "nonebot_plugin_l4d2_server" not in sys.modules:
    dir_ = Path(__file__).parent
    load_plugins(str(dir_ / "nonebot_plugin_l4d2_server"))
