"""关键词屏蔽（``l4_block_keywords``）的回归测试。

包上下文的构造方式同 ``test_reload_paging.py``：``services`` / ``render`` 包不执行
``__init__.py``，``nonebot_plugin_htmlrender`` 用假模块顶替。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock

import a2s
import pytest

INNER_DIR = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"


def _pkg(name: str, path: Path) -> ModuleType:
    """只登记包路径、不执行 ``__init__.py``；已存在就复用。"""
    mod = sys.modules.get(name)
    if mod is None:
        mod = ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod
    return mod


_pkg("nonebot_plugin_l4d2_server", INNER_DIR)
_pkg("nonebot_plugin_l4d2_server.services", INNER_DIR / "services")
_render_pkg = _pkg("nonebot_plugin_l4d2_server.render", INNER_DIR / "render")
if "nonebot_plugin_htmlrender" not in sys.modules:
    _fake_htmlrender = ModuleType("nonebot_plugin_htmlrender")

    async def _unpatched_html_to_pic(*_args, **_kwargs) -> bytes:
        raise RuntimeError("html_to_pic 未在用例里 monkeypatch")

    _fake_htmlrender.html_to_pic = _unpatched_html_to_pic  # type: ignore[attr-defined]
    sys.modules["nonebot_plugin_htmlrender"] = _fake_htmlrender

config = importlib.import_module("nonebot_plugin_l4d2_server.config").config
messages = importlib.import_module("nonebot_plugin_l4d2_server.messages")
ServerRegistry = importlib.import_module(
    "nonebot_plugin_l4d2_server.registry",
).ServerRegistry
server_card = importlib.import_module("nonebot_plugin_l4d2_server.render.server_card")
server_list = importlib.import_module("nonebot_plugin_l4d2_server.render.server_list")
# server_query 用 ``from ..render import ...``，把要用的名字挂到假 render 包上。
_render_pkg.render_server_card = server_card.render_server_card  # type: ignore[attr-defined]
_render_pkg.render_text_card = server_card.render_text_card  # type: ignore[attr-defined]
_render_pkg.render_server_list = server_list.render_server_list  # type: ignore[attr-defined]
blocklist = importlib.import_module("nonebot_plugin_l4d2_server.services.blocklist")
filter_mod = importlib.import_module("nonebot_plugin_l4d2_server.services.filter")
server_query = importlib.import_module(
    "nonebot_plugin_l4d2_server.services.server_query",
)


@pytest.fixture
def keywords(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "l4_block_keywords", ["广告", "外挂|cheat"])


def _info(name: str, *, players: int = 2, down: bool = False) -> a2s.SourceInfo:
    return a2s.SourceInfo(
        protocol=17,
        server_name=name,
        map_name="无" if down else "c2m1_highway",
        folder="left4dead2",
        game="L4D2",
        app_id=550,
        player_count=0 if down else players,
        max_players=0 if down else 8,
        bot_count=0,
        server_type="d",
        platform="l",
        password_protected=False,
        vac_enabled=True,
        version="1.0",
        edf=0,
        ping=0.03,
    )


def _players(*names: str) -> list[a2s.Player]:
    return [
        a2s.Player(index=i, name=n, score=10, duration=60.0)
        for i, n in enumerate(names)
    ]


def test_nothing_blocked_without_keywords(monkeypatch):
    monkeypatch.setattr(config, "l4_block_keywords", [])
    players = _players("外挂哥")
    assert not blocklist.is_blocked("【广告】加群")
    assert blocklist.visible_players(players) is players


@pytest.mark.usefixtures("keywords")
def test_keywords_are_case_insensitive_regex():
    assert blocklist.is_blocked("【广告】加群 123456")
    assert blocklist.is_blocked("CHEAT 服")
    assert not blocklist.is_blocked("Anne云服#1[普通药役]")
    shown = blocklist.visible_players(_players("好人", "外挂哥", "Cheater"))
    assert [p.name for p in shown] == ["好人"]


def test_invalid_pattern_is_skipped(monkeypatch):
    monkeypatch.setattr(config, "l4_block_keywords", ["(", "广告"])
    assert blocklist.is_blocked("广告服"), "其它关键词照常生效"
    assert not blocklist.is_blocked("(")


@pytest.mark.usefixtures("keywords")
async def test_group_query_hides_blocked_servers_and_players(monkeypatch):
    reg = ServerRegistry()
    reg.set_group("云", [{"id": str(i), "ip": f"10.0.0.{i}:27015"} for i in (1, 2, 3)])
    monkeypatch.setattr(server_query, "registry", reg)
    monkeypatch.setattr(
        server_query.L4API,
        "a2s_info_batch",
        AsyncMock(
            return_value=[
                (_info("Anne云服#1[普通药役]"), _players("好人", "外挂哥")),
                (_info("【广告】加群 123456"), _players("路人")),
                (_info("服务器无响应", down=True), []),
            ],
        ),
    )

    out = await server_query.query_group_servers("云")

    assert [s["id_"] for s in out] == ["1", "3"], "服务器名命中的整台去掉"
    assert [p.name for p in out[0]["player"]] == ["好人"], "玩家名命中的只去掉该玩家"
    assert out[0]["server"].player_count == 2, "人数仍按 A2S 上报"


@pytest.mark.usefixtures("keywords")
async def test_single_and_connect_queries_reply_blocked(monkeypatch):
    monkeypatch.setattr(
        server_query.L4API,
        "a2s_info_batch",
        AsyncMock(return_value=[(_info("【广告】加群"), _players("路人"))]),
    )
    card = AsyncMock(return_value=b"card")
    monkeypatch.setattr(server_query, "render_server_card", card)

    assert (
        await server_query._render_single("10.0.0.2", 27015, is_img=True)
        == messages.Sm.server_blocked
    )
    assert (
        await server_query.get_ip_server("10.0.0.2:27015") == messages.Sm.server_blocked
    )
    card.assert_not_awaited()


@pytest.mark.usefixtures("keywords")
async def test_single_card_hides_blocked_players(monkeypatch):
    monkeypatch.setattr(
        server_query.L4API,
        "a2s_info_batch",
        AsyncMock(
            return_value=[(_info("Anne云服#1[普通药役]"), _players("好人", "外挂哥"))],
        ),
    )
    card = AsyncMock(return_value=b"card")
    monkeypatch.setattr(server_query, "render_server_card", card)

    assert await server_query._render_single("10.0.0.1", 27015, is_img=True) == b"card"
    assert [p.name for p in card.await_args.args[1]] == ["好人"]


@pytest.mark.usefixtures("keywords")
async def test_pickers_skip_blocked_servers_but_judge_by_real_players(monkeypatch):
    """tj/zl/kl 不选被屏蔽的服；条件仍按真实玩家列表算（被隐藏的玩家也在服里）。"""
    infos = {
        1: (_info("【广告】空服", players=0), []),
        2: (_info("Anne云服#2[普通药役]", players=1), _players("外挂哥")),
        3: (_info("Anne云服#3[普通药役]", players=0), []),
    }

    async def batch(ips, **_kwargs):
        return [infos[ips[0][1]]]

    monkeypatch.setattr(filter_mod.L4API, "a2s_info_batch", batch)
    servers = [{"host": "10.0.0.1", "port": port} for port in (1, 2, 3)]

    picked = await filter_mod.filter_servers(servers, "kl")

    assert [s["port"] for s in picked] == [3]
