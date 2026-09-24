"""Project-level constants: paths, defaults, command names."""

from __future__ import annotations

from pathlib import Path

# 收藏 / 订阅 / 黑名单相关持久化文件名（位于 localstore 管理的 data 根目录下）。
FAVORITES_FILENAME = "favorites.json"
NOTIFY_STATE_FILENAME = "notify_state.json"
BLOCKLIST_FILENAME = "blocklist.json"

# 包内资源路径
FONT_PATH = Path(__file__).parent / "render" / "fonts" / "loli.ttf"
HELP_DATA_PATH = Path(__file__).parent / "render" / "help" / "Help.json"
HELP_TEXTURES_PATH = Path(__file__).parent / "render" / "help" / "textures"
HELP_ICONS_PATH = Path(__file__).parent / "render" / "help" / "icons"
RENDER_TEMPLATES_PATH = Path(__file__).parent / "render" / "templates"
RENDER_BACKGROUNDS_PATH = Path(__file__).parent / "render" / "backgrounds"

# 图片质量
JPEG_QUALITY = 95

# A2S 默认端口
DEFAULT_GAME_PORT = 20715

# 筛选模式
FILTER_MODES = ("tj", "zl", "kl")
DEFAULT_MAP_TYPES = ("普通药役", "硬核药役")

# 旧版文件名
LEGACY_URL_FILENAME = "l4d2.json"
LEGACY_GROUP_SUBDIR = "l4d2"
SB_PAGES_FILENAME = "sb_pages.json"

# data 根目录下这些 JSON 不是服务器组：registry 扫描、l4列组 / 导出都要跳过，
# 否则 notify_state.json 的 "host:port" 键会被当成组名注册成指令。
NON_GROUP_FILENAMES = frozenset(
    {
        FAVORITES_FILENAME,
        NOTIFY_STATE_FILENAME,
        BLOCKLIST_FILENAME,
        LEGACY_URL_FILENAME,
        SB_PAGES_FILENAME,
    },
)
