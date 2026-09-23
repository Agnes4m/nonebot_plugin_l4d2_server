"""重载刷新内存 / 大组分页出图 / 出图兜底 / 长消息切段 的回归测试。

照 ``test_a2s_cache.py`` 的做法手工构造包上下文，只加载要测的模块：
``services`` / ``render`` 两个包不执行 ``__init__.py``（会连带导入全部服务、
alconna、htmlrender）；``nonebot_plugin_htmlrender`` 用假模块顶替，出图函数
在各个用例里按需 monkeypatch。NoneBot 本身由 conftest 初始化。
"""

from __future__ import annotations

import asyncio
import importlib
import io
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock

import a2s
import pytest
from PIL import Image

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

config_mod = importlib.import_module("nonebot_plugin_l4d2_server.config")
messages = importlib.import_module("nonebot_plugin_l4d2_server.messages")
path_resolver = importlib.import_module(
    "nonebot_plugin_l4d2_server.services.path_resolver",
)
registry_mod = importlib.import_module("nonebot_plugin_l4d2_server.registry")
groups_store = importlib.import_module("nonebot_plugin_l4d2_server.store.groups")
server_card = importlib.import_module("nonebot_plugin_l4d2_server.render.server_card")
server_list = importlib.import_module("nonebot_plugin_l4d2_server.render.server_list")
# server_query 用 ``from ..render import ...``，把要用的名字挂到假 render 包上。
_render_pkg.render_server_card = server_card.render_server_card  # type: ignore[attr-defined]
_render_pkg.render_text_card = server_card.render_text_card  # type: ignore[attr-defined]
_render_pkg.render_server_list = server_list.render_server_list  # type: ignore[attr-defined]
server_query = importlib.import_module(
    "nonebot_plugin_l4d2_server.services.server_query"
)
sourceban = importlib.import_module("nonebot_plugin_l4d2_server.services.sourceban")

config = config_mod.config
ServerRegistry = registry_mod.ServerRegistry


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(path_resolver, "_data_dir", tmp_path)
    return tmp_path


@pytest.fixture
def reg(monkeypatch: pytest.MonkeyPatch) -> ServerRegistry:
    """换一个干净的 registry 给 sourceban 用，不碰模块级单例。"""
    fresh = ServerRegistry()
    monkeypatch.setattr(sourceban, "registry", fresh)
    return fresh


def _write(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _servers(n: int, prefix: str = "10.0.0") -> list[dict]:
    return [{"id": str(i), "ip": f"{prefix}.{i}:27015"} for i in range(1, n + 1)]


# ---------------- split_message ----------------


def test_split_message_packs_lines_under_limit():
    lines = [f"云{i}  3/8  c2m1_highway  服务器名字" for i in range(200)]
    chunks = messages.split_message(lines, max_chars=500)
    assert len(chunks) > 1
    assert all(len(c) <= 500 for c in chunks)
    assert "\n".join(chunks).split("\n") == lines, "按行切，拼回去和原文一致"


def test_split_message_hard_cuts_overlong_line():
    chunks = messages.split_message(["x" * 1200], max_chars=500)
    assert [len(c) for c in chunks] == [500, 500, 200]


def test_split_message_empty():
    assert messages.split_message([]) == []


# ---------------- registry 重载 ----------------


async def test_reload_keeps_alias(data_dir: Path):
    """anne 这类别名不能被 l4reload / l4reloadsb 的重载清掉。"""
    _write(data_dir / "云.json", {"云": _servers(3)})
    reg = ServerRegistry()
    await reg.load_all()
    reg.add_command("anne")
    await reg.load_all()
    assert {"anne", "云"} <= reg.commands
    assert reg.get("anne") is None


async def test_non_group_files_are_ignored(data_dir: Path):
    _write(data_dir / "云.json", {"云": _servers(2)})
    _write(data_dir / "notify_state.json", {"1.2.3.4:27015": {"online": True}})
    _write(data_dir / "favorites.json", [{"tag": "云"}])
    _write(data_dir / "sb_pages.json", {"云": "https://example.invalid/"})
    reg = ServerRegistry()
    await reg.load_all()
    assert reg.commands == {"云"}
    assert await groups_store.list_groups() == ["云"]


async def test_tag_file_wins_over_stale_duplicates(data_dir: Path):
    """刷新写的是 ``<组名>.json``，其它文件里的同名旧数据不能把它盖掉。"""
    _write(data_dir / "multi.json", {"云": _servers(1, "9.9.9"), "呆呆": _servers(1)})
    _write(data_dir / "l4d2" / "云.json", {"云": _servers(2, "8.8.8")})
    _write(data_dir / "云.json", {"云": _servers(5)})
    reg = ServerRegistry()
    await reg.load_all()
    assert [e["ip"] for e in reg.get("云")] == [
        f"10.0.0.{i}:27015" for i in range(1, 6)
    ]
    assert reg.get("呆呆") is not None


async def test_reload_never_exposes_empty_state(data_dir: Path):
    """重载途中进来的查询要么拿到旧数据要么拿到新数据，不会拿到空组。"""
    _write(data_dir / "云.json", {"云": _servers(5)})
    reg = ServerRegistry()
    await reg.load_all()
    seen_missing = False

    async def reader() -> None:
        nonlocal seen_missing
        for _ in range(300):
            if not reg.get("云"):
                seen_missing = True
            await asyncio.sleep(0)

    await asyncio.gather(reader(), *(reg.load_all() for _ in range(5)))
    assert not seen_missing


# ---------------- SourceBans 刷新 ----------------


async def test_empty_scrape_keeps_group(data_dir: Path, reg, monkeypatch):
    """SourceBans 挂了返回空列表时，不能把整组写空。"""
    _write(data_dir / "云.json", {"云": _servers(4)})
    _write(data_dir / "sb_pages.json", {"云": "https://example.invalid/"})
    monkeypatch.setattr(sourceban.L4API, "get_sourceban", AsyncMock(return_value=[]))

    ok, fails = await sourceban.refresh_all_pages()

    assert ok == 0
    assert len(fails) == 1 and "已保留原有列表" in fails[0]
    assert len(json.loads((data_dir / "云.json").read_text("utf-8"))["云"]) == 4
    assert len(reg.get("云")) == 4


async def test_refresh_all_pages_reloads_memory_once(data_dir: Path, reg, monkeypatch):
    _write(
        data_dir / "sb_pages.json",
        {"云": "https://a.invalid/", "呆呆": "https://b.invalid/"},
    )
    scraped = [
        sourceban.SourceBansInfo(index=i, host="1.2.3.4", port=27015 + i)
        for i in range(3)
    ]
    monkeypatch.setattr(
        sourceban.L4API, "get_sourceban", AsyncMock(return_value=scraped)
    )
    reg.add_command("anne")
    sourceban.L4API._cache[("5.6.7.8", 1)] = (float("inf"), (None, []))
    real_load = reg.load_all
    load_calls = 0

    async def counting_load() -> None:
        nonlocal load_calls
        load_calls += 1
        await real_load()

    monkeypatch.setattr(reg, "load_all", counting_load)

    ok, fails = await sourceban.refresh_all_pages()

    assert (ok, fails) == (2, [])
    assert load_calls == 1, "两个组都写完盘后只重载一次"
    assert [e["ip"] for e in reg.get("云")] == [
        f"1.2.3.4:{27015 + i}" for i in range(3)
    ]
    assert "anne" in reg.commands
    assert not sourceban.L4API._cache, "刷新后 A2S 缓存应被清空"


# ---------------- 组查询分页 ----------------


def _info(i: int, *, players: int = 3, down: bool = False) -> a2s.SourceInfo:
    return a2s.SourceInfo(
        protocol=17,
        server_name="服务器无响应" if down else f"Anne云服#{i}[普通药役][8特20秒]",
        map_name="c2m1_highway",
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
        steam_id=i - 1,
    )


def _out(
    n: int,
    *,
    offline: set[int] | frozenset[int] = frozenset(),
    empty: set[int] | frozenset[int] = frozenset(),
) -> list[dict]:
    """``n`` 台服：``offline`` 里的不在线，``empty`` 里的在线但没人，其余 3 人。"""
    return [
        {
            "server": _info(i, players=0 if i in empty else 3, down=i in offline),
            "player": [],
            "host": "10.0.0.1",
            "port": 27015 + i,
            "command": "云",
            "id_": i,
        }
        for i in range(1, n + 1)
    ]


async def _collect(
    command: str = "云",
    *,
    is_img: bool = True,
    show_all: bool = False,
) -> list:
    return [
        part
        async for part in server_query.iter_group_output(
            command,
            is_img=is_img,
            show_all=show_all,
        )
    ]


@pytest.fixture
def paging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "l4_image_page_size", 30)
    monkeypatch.setattr(config, "l4_image_max_servers", 0)


def _mock_query(monkeypatch: pytest.MonkeyPatch, servers: list[dict]) -> None:
    monkeypatch.setattr(
        server_query, "query_group_servers", AsyncMock(return_value=servers)
    )


def _mock_render(monkeypatch: pytest.MonkeyPatch, **kwargs) -> AsyncMock:
    render = AsyncMock(**kwargs)
    monkeypatch.setattr(server_query, "render_server_list", render)
    return render


@pytest.mark.usefixtures("paging")
async def test_default_shows_only_servers_with_players(monkeypatch):
    """「云」默认只列有人的服务器；没人 / 不在线的都不画，也不附不在线列表。"""
    _mock_query(monkeypatch, _out(10, offline={9, 10}, empty={2, 3, 4, 5, 6}))
    render = _mock_render(monkeypatch, return_value=b"img")

    assert await _collect() == [b"img"]
    call = render.await_args
    assert [s["id_"] for s in call.args[0]] == [1, 7, 8]
    assert call.kwargs["heading"] == "云 有人的服务器 3 台 (在线 8/10 台)"
    assert "云全" in call.kwargs["hint"]
    assert call.kwargs["offline_ids"] == []


@pytest.mark.usefixtures("paging")
async def test_show_all_lists_everything_split_into_pages(monkeypatch):
    """「云全」列出全部在线服（含没人的），按每页 30 台拆图，不在线列表只放最后一页。"""
    _mock_query(monkeypatch, _out(105, offline={7, 50}, empty=set(range(60, 106))))
    render = _mock_render(
        monkeypatch, side_effect=lambda servers, **_kw: bytes(len(servers))
    )

    parts = await _collect(show_all=True)

    assert [len(p) for p in parts] == [30, 30, 30, 13], (
        "103 台在线 → 30/30/30/13 四张图"
    )
    calls = render.await_args_list
    assert [c.kwargs["heading"] for c in calls] == [
        f"已加载服务器 云 (在线 103/105 台) · 第 {n}/4 页" for n in range(1, 5)
    ]
    assert {c.kwargs["hint"] for c in calls} == {""}
    assert [c.kwargs["offline_ids"] for c in calls] == [[], [], [], ["云7", "云50"]]


@pytest.mark.usefixtures("paging")
async def test_default_mode_also_splits_into_pages(monkeypatch):
    _mock_query(monkeypatch, _out(100, empty=set(range(71, 101))))
    render = _mock_render(
        monkeypatch, side_effect=lambda servers, **_kw: bytes(len(servers))
    )

    parts = await _collect()

    assert [len(p) for p in parts] == [30, 30, 10]
    assert render.await_args_list[0].kwargs["heading"] == (
        "云 有人的服务器 70 台 (在线 100/100 台) · 第 1/3 页"
    )


@pytest.mark.usefixtures("paging")
async def test_no_one_playing_replies_with_hint(monkeypatch):
    _mock_query(monkeypatch, _out(5, offline={5}, empty={1, 2, 3, 4}))
    render = _mock_render(monkeypatch, return_value=b"img")

    parts = await _collect()

    render.assert_not_awaited()
    assert len(parts) == 1 and isinstance(parts[0], str)
    assert (
        "没有有人的服务器" in parts[0]
        and "在线 4/5 台" in parts[0]
        and "云全" in parts[0]
    )
    assert await _collect(show_all=True) == [b"img"], "云全 照样出图"


@pytest.mark.usefixtures("paging")
async def test_browser_failure_falls_back_to_plain_images(monkeypatch):
    """某页浏览器出图失败后，这一页和后面的页都走 PIL 简易图，不再每页等一次超时。"""
    _mock_query(monkeypatch, _out(75, offline={3}))
    render = _mock_render(monkeypatch, side_effect=[b"page1", None])

    parts = await _collect()

    assert render.await_count == 2
    assert parts[0] == b"page1"
    assert len(parts) == 3
    for pic in parts[1:]:
        assert Image.open(io.BytesIO(pic)).format == "JPEG"


@pytest.mark.usefixtures("paging")
async def test_show_all_when_everything_offline_renders_one_page(monkeypatch):
    _mock_query(monkeypatch, _out(4, offline={1, 2, 3, 4}))
    render = _mock_render(monkeypatch, return_value=b"img")

    assert await _collect(show_all=True) == [b"img"]
    assert render.await_args.args[0] == []
    assert render.await_args.kwargs["offline_ids"] == ["云1", "云2", "云3", "云4"]


async def test_text_mode_follows_the_same_filter(monkeypatch):
    _mock_query(monkeypatch, _out(150, offline={9}, empty={10}))
    render = _mock_render(monkeypatch)

    default = "\n".join(await _collect(is_img=False))
    parts = await _collect(is_img=False, show_all=True)

    render.assert_not_awaited()
    assert "云9  离线" not in default and "云10  0/8" not in default
    assert "云1  3/8" in default and "云全" in default
    assert len(parts) > 1
    assert all(isinstance(p, str) and len(p) <= messages.MAX_TEXT_CHARS for p in parts)
    everything = "\n".join(parts)
    assert (
        "云9  离线" in everything
        and "云10  0/8" in everything
        and "云150  3/8" in everything
    )


async def test_empty_group_yields_nothing(monkeypatch):
    _mock_query(monkeypatch, [])
    assert await _collect() == []
    assert await _collect(show_all=True) == []


# ---------------- 服务器名去前缀 ----------------


@pytest.mark.parametrize(
    ("raw", "shown"),
    [
        (
            "Anne云服#57[普通药役][缺人][无MOD][8特20秒]",
            "[普通药役][缺人][无MOD][8特20秒]",
        ),
        ("Anne Server #27[HT训练][2特0秒]", "[HT训练][2特0秒]"),
        ("Anne云服#1", "Anne云服#1"),  # 只有前缀时保留原名
        ("[别家]Anne云服#3[普通药役]", "[别家]Anne云服#3[普通药役]"),  # 不在开头不动
        ("服务器无响应", "服务器无响应"),
    ],
)
def test_display_name_strips_anne_prefix(raw, shown):
    assert server_query.display_name(raw) == shown


@pytest.mark.parametrize(
    ("pattern", "shown"),
    [
        (r"^Anne[^#\[]*", "#57[普通药役]"),  # 只去 Anne云服、保留编号
        ("", "Anne云服#57[普通药役]"),  # 留空不处理
        ("(", "Anne云服#57[普通药役]"),  # 非法正则：忽略，不抛异常
    ],
)
def test_display_name_pattern_is_configurable(pattern, shown, monkeypatch):
    monkeypatch.setattr(config, "l4_name_strip_pattern", pattern)
    assert server_query.display_name("Anne云服#57[普通药役]") == shown


async def test_query_group_servers_fills_display_name(monkeypatch):
    reg = ServerRegistry()
    reg.set_group("云", [{"id": "57", "ip": "10.0.0.1:27015"}])
    monkeypatch.setattr(server_query, "registry", reg)
    monkeypatch.setattr(
        server_query.L4API,
        "a2s_info_batch",
        AsyncMock(return_value=[(_info(57), [])]),
    )

    (out,) = await server_query.query_group_servers("云")

    assert out["name"] == "[普通药役][8特20秒]"
    assert out["server"].server_name == "Anne云服#57[普通药役][8特20秒]", "A2S 原名不改"


# ---------------- Chromium 出图：重试 / 超时 ----------------


async def test_screenshot_retries_once_after_crash(monkeypatch):
    calls = 0

    async def flaky(*_args, **_kwargs) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("Target page, context or browser has been closed")
        return b"jpeg"

    monkeypatch.setattr(server_list, "html_to_pic", flaky)
    assert await server_list._screenshot("<html></html>") == b"jpeg"
    assert calls == 2


async def test_screenshot_gives_up_after_second_crash(monkeypatch):
    broken = AsyncMock(side_effect=RuntimeError("browser has been closed"))
    monkeypatch.setattr(server_list, "html_to_pic", broken)
    assert await server_list._screenshot("<html></html>") is None
    assert broken.await_count == 2


async def test_screenshot_timeout_is_not_retried(monkeypatch):
    calls = 0

    async def slow(*_args, **_kwargs) -> bytes:
        nonlocal calls
        calls += 1
        await asyncio.sleep(5)
        return b"late"

    monkeypatch.setattr(config, "l4_render_timeout", 0.05)
    monkeypatch.setattr(server_list, "html_to_pic", slow)
    assert await server_list._screenshot("<html></html>") is None
    assert calls == 1


@pytest.mark.usefixtures("data_dir")
@pytest.mark.parametrize("style", ["default", "old"])
async def test_page_html_has_heading_names_and_background(style, monkeypatch):
    monkeypatch.setattr(config, "l4_style", style)
    seen: dict = {}

    async def capture(html: str, **kwargs) -> bytes:
        seen["html"], seen["kwargs"] = html, kwargs
        return b"jpeg"

    monkeypatch.setattr(server_list, "html_to_pic", capture)
    page = _out(3)
    page[0]["name"] = "[普通药役][8特20秒]"
    pic = await server_list.render_server_list(
        page,
        heading="云 有人的服务器 70 台 (在线 100/105 台) · 第 2/4 页",
        hint="只显示有人的服务器，发送「云全」查看全部",
        offline_ids=["云7"],
    )

    assert pic == b"jpeg"
    assert seen["kwargs"]["type"] == "jpeg"
    html = seen["html"]
    assert "云 有人的服务器 70 台 (在线 100/105 台) · 第 2/4 页" in html
    assert "发送「云全」查看全部" in html
    assert "云1:[普通药役][8特20秒]" in html, "卡片用去掉前缀的名字"
    assert "云2:Anne云服#2[普通药役]" in html, "没给 name 时回退到 A2S 原名"
    if style == "default":
        assert "url('file://" in html, "背景图直接引用原文件，不再复制进包目录"
        assert "云7" in html


# ---------------- PIL 兜底图 ----------------


def test_text_card_grows_with_content():
    short = Image.open(io.BytesIO(server_card.render_text_card("标题", ["一行"])))
    many = Image.open(
        io.BytesIO(
            server_card.render_text_card("标题", [f"第 {i} 行" for i in range(40)])
        ),
    )
    wrapped = Image.open(
        io.BytesIO(server_card.render_text_card("标题", ["很长" * 200]))
    )
    assert short.format == many.format == "JPEG"
    assert many.height > short.height
    assert wrapped.height > short.height, "超宽的行要换行而不是被裁掉"
