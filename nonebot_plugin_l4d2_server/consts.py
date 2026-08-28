"""Project-level constants: paths, defaults, command names."""

from __future__ import annotations

from pathlib import Path

# 数据目录（相对 bot 工作目录）
DEFAULT_DATA_DIR = "data/L4D2"

# 旧版布局（迁移完成后将不再使用；保留以支持向后兼容读取）
LEGACY_GROUP_DIR = Path(DEFAULT_DATA_DIR) / "l4d2"
LEGACY_URL_FILE = Path(DEFAULT_DATA_DIR) / "l4d2.json"

# 字体资源路径（包内）
FONT_PATH = Path(__file__).parent / "render" / "fonts" / "loli.ttf"

# 帮助图资源路径（包内）
HELP_DATA_PATH = Path(__file__).parent / "render" / "help" / "Help.json"
HELP_TEXTURES_PATH = Path(__file__).parent / "render" / "help" / "textures"
HELP_ICONS_PATH = Path(__file__).parent / "render" / "help" / "icons"

# HTML 渲染模板路径
RENDER_TEMPLATES_PATH = Path(__file__).parent / "render" / "templates"
RENDER_BACKGROUNDS_PATH = Path(__file__).parent / "render" / "backgrounds"

# 用户自定义背景目录（运行时写入；用户可在 data/L4D2/custom_backgrounds/ 放置图片）
CUSTOM_BACKGROUNDS_PATH = Path(DEFAULT_DATA_DIR) / "custom_backgrounds"

# 图片生成质量
JPEG_QUALITY = 95

# 默认端口（A2S 默认）
DEFAULT_GAME_PORT = 20715

# 筛选模式
FILTER_MODES = ("tj", "zl", "kl")
DEFAULT_MAP_TYPES = ("普通药役", "硬核药役")
