"""Pytest configuration.

Initialises a minimal nonebot runtime so the inner package's
``config.get_plugin_config(...)`` call works during test collection
(imports of the inner modules run before fixtures).
"""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path

# Make the inner package importable as top-level modules for tests.
INNER = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"
sys.path.insert(0, str(INNER))


def _ensure_nonebot() -> None:
    """Initialise nonebot with an empty env if not already up."""
    if "nonebot" not in sys.modules:
        return
    import nonebot  # type: ignore[import-not-found]

    try:
        from nonebot import get_driver  # type: ignore[import-not-found]
        get_driver()
        return
    except ValueError:
        pass

    nonebot.init(env=types.SimpleNamespace(), _env_file=None)


# Run at import time (before any test collection).
_ensure_nonebot()
logging.getLogger("nonebot").setLevel(logging.CRITICAL)


def pytest_configure(config):
    """Reset driver config so sub-tests with patched paths still work."""
    pass