"""兼容转发层 - 请迁移到 core.help"""

from __future__ import annotations

from ..core.help import *  # noqa: F403
from ..core.help import __version__ as _  # noqa: F401

__version__ = "1.3.1"
