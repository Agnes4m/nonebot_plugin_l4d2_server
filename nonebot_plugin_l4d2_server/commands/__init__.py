"""Command handlers — thin layer that delegates to ``services``.

Import order matters: ``query`` defines the shared ``l4_request`` matcher
and ``refresh_server_command_rule`` helper used by ``ban`` / ``admin`` /
``server_mgmt``。``server_mgmt`` / ``favorite`` 不依赖 ``query``，但放在
``query`` 之前便于 ``__init__`` 在启动期统一扫描。
"""

from . import admin, ban, favorite, local, query, server_mgmt  # noqa: F401

__all__ = ["admin", "ban", "favorite", "local", "query", "server_mgmt"]
