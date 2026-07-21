from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_set_group_refreshes_runtime_registry(monkeypatch, tmp_path: Path):
    from nonebot_plugin_l4d2_server.server import ban

    group_path = tmp_path / "云.json"
    set_group = AsyncMock(return_value=group_path)
    reload_ip = Mock()
    refresh_server_command_rule = Mock()
    servers = ["server.example:27015"]

    monkeypatch.setattr(ban, "set_group", set_group)
    monkeypatch.setattr(ban, "reload_ip", reload_ip)
    monkeypatch.setattr(
        ban,
        "refresh_server_command_rule",
        refresh_server_command_rule,
    )

    result = await ban._set_group_and_refresh("云", servers)  # noqa: SLF001

    assert result == group_path
    set_group.assert_awaited_once_with("云", servers)
    reload_ip.assert_called_once_with()
    refresh_server_command_rule.assert_called_once_with(ban.l4_request)
