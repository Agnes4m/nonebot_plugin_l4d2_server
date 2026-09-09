"""Project-level constants: paths, defaults, command names."""

from __future__ import annotations

from pathlib import Path

# ``l4_path`` 默认值（相对 bot 工作目录）；运行时权威值在 ``config.data_dir``。
DEFAULT_DATA_DIR = "data/L4D2"

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
