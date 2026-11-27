"""A2S 缓存语义冒烟测试。

只覆盖 ``L4D2Api._a2s_one`` / ``a2s_info_batch`` 的关键不变量：
缓存命中、TTL=0 禁用、deepcopy 隔离、并发=0 不走 Semaphore。
不依赖真实 UDP / Source 服务器。

测试用 ``importlib`` 显式构造 ``nonebot_plugin_l4d2_server.api.l4d2``
模块上下文，使其相对导入（``from ..config import config``）正常工作。
这样不依赖已有测试的 sys.path / conftest hack，单文件可独立跑。
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, patch

INNER_DIR = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"


def _load(name: str, path: Path) -> ModuleType:
    # 其它测试文件先加载过就复用：重新执行会换掉 sys.modules 里的 config，
    # 已导入的模块和之后的测试就不再指向同一个 config 对象，monkeypatch 失效。
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# 构造一个空的 nonebot_plugin_l4d2_server 包，避免子模块导入时找不到包。
if "nonebot_plugin_l4d2_server" not in sys.modules:
    _pkg_root = ModuleType("nonebot_plugin_l4d2_server")
    _pkg_root.__path__ = [str(INNER_DIR)]
    sys.modules["nonebot_plugin_l4d2_server"] = _pkg_root

# 按依赖顺序加载内部模块。
_load("nonebot_plugin_l4d2_server.consts", INNER_DIR / "consts.py")
_load("nonebot_plugin_l4d2_server.http_helpers", INNER_DIR / "http_helpers.py")
config_module = _load(
    "nonebot_plugin_l4d2_server.config",
    INNER_DIR / "config.py",
)
_load("nonebot_plugin_l4d2_server.api.models", INNER_DIR / "api" / "models.py")
_load("nonebot_plugin_l4d2_server.api.sources", INNER_DIR / "api" / "sources.py")
api_module = _load(
    "nonebot_plugin_l4d2_server.api.l4d2",
    INNER_DIR / "api" / "l4d2.py",
)

L4D2Api = api_module.L4D2Api
import a2s  # noqa: E402  加载 l4d2 之后才能拿到 a2s.SourceInfo


def _make_source_info() -> a2s.SourceInfo:
    return a2s.SourceInfo(
        protocol=0,
        server_name="test",
        map_name="m",
        folder="m",
        game="L4D2",
        app_id=1,
        steam_id=0,
        player_count=2,
        max_players=8,
        bot_count=0,
        server_type="w",
        platform="w",
        password_protected=False,
        vac_enabled=False,
        version="1.0",
        edf=0,
        ping=0,
    )


class _Patch:
    """``with _Patch(obj, attr, value):`` 临时改属性。"""

    def __init__(self, obj, attr, value):
        self.obj = obj
        self.attr = attr
        self.value = value
        self.original = getattr(obj, attr, None)

    def __enter__(self):
        setattr(self.obj, self.attr, self.value)
        return self

    def __exit__(self, *exc):
        if self.original is None:
            with contextlib.suppress(AttributeError):
                delattr(self.obj, self.attr)
        else:
            setattr(self.obj, self.attr, self.original)


def _fresh_api(ttl: int = 15, concurrency: int = 0, timeout: float = 2.5) -> L4D2Api:
    with (
        _Patch(config_module.config, "l4_a2s_cache_ttl", ttl),
        _Patch(
            config_module.config,
            "l4_a2s_concurrency",
            concurrency,
        ),
        _Patch(config_module.config, "l4_a2s_timeout", timeout),
    ):
        return L4D2Api()


def _fresh_probe_api(
    *,
    ttl: int = 15,
    concurrency: int = 0,
    timeout: float = 2.5,
    probe_timeout: float = 1.0,
    passes: int = 2,
    probe_concurrency: int = 0,
    neg_ttl: int = 60,
) -> L4D2Api:
    with (
        _Patch(config_module.config, "l4_a2s_cache_ttl", ttl),
        _Patch(config_module.config, "l4_a2s_concurrency", concurrency),
        _Patch(config_module.config, "l4_a2s_timeout", timeout),
        _Patch(config_module.config, "l4_a2s_probe_timeout", probe_timeout),
        _Patch(config_module.config, "l4_a2s_probe_passes", passes),
        _Patch(config_module.config, "l4_a2s_probe_concurrency", probe_concurrency),
        _Patch(config_module.config, "l4_a2s_negative_ttl", neg_ttl),
    ):
        return L4D2Api()


def test_cache_hit_skips_udp_call():
    """第二次同 IP 查询应直接读缓存，不打 a2s.ainfo。"""
    api = _fresh_api(ttl=15)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    aplayers_mock = AsyncMock(return_value=[])
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        asyncio.run(api.a2s_info_batch(ips, want_players=True))
        assert ainfo_mock.await_count == 1
        assert aplayers_mock.await_count == 1

        asyncio.run(api.a2s_info_batch(ips, want_players=True))
        assert ainfo_mock.await_count == 1, "缓存命中应跳过 ainfo"
        assert aplayers_mock.await_count == 1, "缓存命中应跳过 aplayers"


def test_cache_disabled_when_ttl_zero():
    api = _fresh_api(ttl=0)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    aplayers_mock = AsyncMock(return_value=[])
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        asyncio.run(api.a2s_info_batch(ips))
        asyncio.run(api.a2s_info_batch(ips))
        assert ainfo_mock.await_count == 2
        assert aplayers_mock.await_count == 2


def test_cache_deepcopy_isolation():
    """下游 mutate 返回值不应污染缓存。"""
    api = _fresh_api(ttl=15)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    aplayers_mock = AsyncMock(return_value=[])
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        first = asyncio.run(api.a2s_info_batch(ips, want_players=False))[0]
        original_name = first[0].server_name
        # ``_a2s_one`` 往缓存里放的是 deepcopy，返回的 server 和缓存条目独立；
        # mutate 返回值不应影响缓存里的 server_name。
        first[0].server_name = "被改写过"

        second = asyncio.run(api.a2s_info_batch(ips, want_players=False))[0]
        assert second[0].server_name == original_name, "第二次读取应来自未污染的缓存"
        # 缓存里的 server_name 也不应被影响
        cached_server = api._cache[api._cache_key(ips[0])][1][0]
        assert cached_server.server_name == original_name, "缓存条目本身不应被污染"


def test_mutating_returned_players_keeps_cache_clean():
    """出图会给 ``player.name`` 追加时长；缓存未命中路径返回的玩家也不能和缓存共用对象，
    否则 TTL 内第二次查询会看到 ``名字 | 1h | 1h`` 这种重复后缀。"""
    api = _fresh_api(ttl=15)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    aplayers_mock = AsyncMock(
        return_value=[a2s.Player(index=0, name="p1", score=3, duration=60.0)],
    )
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        first = asyncio.run(api.a2s_info_batch(ips, want_players=True))[0]
        first[1][0].name += " | 1m 0s"

        second = asyncio.run(api.a2s_info_batch(ips, want_players=True))[0]
        assert aplayers_mock.await_count == 1, "第二次应命中缓存"
        assert second[1][0].name == "p1", "缓存里的玩家名不应被下游修改污染"


def test_players_not_fetched_do_not_satisfy_player_query():
    """``want_players=False`` 写进缓存的条目没有玩家列表，之后要玩家的查询
    必须重新查，不能拿到「没人」。"""
    api = _fresh_api(ttl=15)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    aplayers_mock = AsyncMock(
        return_value=[a2s.Player(index=0, name="p1", score=3, duration=60.0)],
    )
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        asyncio.run(api.a2s_info_batch(ips, want_players=False))
        assert aplayers_mock.await_count == 0

        ((_, players),) = asyncio.run(api.a2s_info_batch(ips, want_players=True))
        assert aplayers_mock.await_count == 1, "缓存条目没查过玩家，应重新查"
        assert [p.name for p in players] == ["p1"]

        # 查过玩家之后，不要玩家的查询照样命中缓存
        asyncio.run(api.a2s_info_batch(ips, want_players=False))
        assert ainfo_mock.await_count == 2


def test_clear_cache_forces_requery():
    api = _fresh_api(ttl=15)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            AsyncMock(return_value=[]),
        ),
    ):
        asyncio.run(api.a2s_info_batch(ips))
        api.clear_cache()
        asyncio.run(api.a2s_info_batch(ips))
        assert ainfo_mock.await_count == 2, "clear_cache 之后应重新走网络"


def test_concurrency_zero_uses_no_semaphore():
    api = _fresh_api(concurrency=0)
    assert api._sem is None

    api_with_cap = _fresh_api(concurrency=8)
    assert api_with_cap._sem is not None
    assert api_with_cap._sem._value == 8


def test_ainfo_failure_skips_aplayers():
    """ainfo 抛异常 → 标记 want_players=False，不再调 aplayers。"""
    api = _fresh_api()
    ainfo_mock = AsyncMock(side_effect=ConnectionError("simulated UDP fail"))
    aplayers_mock = AsyncMock(return_value=[])
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        results = asyncio.run(api.a2s_info_batch(ips, want_players=True))
        assert ainfo_mock.await_count == 1
        assert aplayers_mock.await_count == 0, "ainfo 失败时不应再调 aplayers"
        assert results[0][0].max_players == 0


def test_cache_expires_after_ttl():
    api = _fresh_api(ttl=15)
    ainfo_mock = AsyncMock(return_value=_make_source_info())
    aplayers_mock = AsyncMock(return_value=[])
    ips = [("1.2.3.4", 27015)]

    with (
        patch.object(api_module.a2s, "ainfo", ainfo_mock),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        asyncio.run(api.a2s_info_batch(ips))
        assert ainfo_mock.await_count == 1

        # 模拟过期：把 expire_at 改成过去
        key = api._cache_key(ips[0])
        _, value = api._cache[key]
        api._cache[key] = (time.monotonic() - 1, value)

        asyncio.run(api.a2s_info_batch(ips))
        assert ainfo_mock.await_count == 2, "TTL 过期应重新走网络"


def test_batch_orders_results_by_steam_id():
    """``a2s_info_batch`` 按 steam_id 升序返回，与输入 IP 顺序无关。

    steam_id 是 ``_a2s_one`` 里 ``server.steam_id = index``（enumerate
    index）写入的，不依赖服务端返回。
    """
    api = _fresh_api()

    async def fake_ainfo(ip, **_kwargs):
        # 服务端给的 steam_id 故意乱序，且与最终 steam_id 不一致——
        # 验证 ``_a2s_one`` 一定覆盖成 enumerate index。
        await asyncio.sleep(0)
        idx_map = {
            ("1.1.1.1", 27015): 99,
            ("2.2.2.2", 27015): 99,
            ("3.3.3.3", 27015): 99,
        }
        info = _make_source_info()
        info.steam_id = idx_map[ip]
        return info

    aplayers_mock = AsyncMock(return_value=[])
    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(
            api_module.a2s,
            "aplayers",
            aplayers_mock,
        ),
    ):
        results = asyncio.run(
            api.a2s_info_batch(
                [("1.1.1.1", 27015), ("2.2.2.2", 27015), ("3.3.3.3", 27015)],
                want_players=False,
            ),
        )

    steam_ids = [r[0].steam_id for r in results]
    assert steam_ids == [0, 1, 2], f"应按 steam_id 升序，实际 {steam_ids}"


# ---------------- 组查询快扫（probe=True）：两轮短超时 + 负缓存 + 补玩家 ----------------


def _probe_info(name: str = "ok", players: int = 2) -> a2s.SourceInfo:
    info = _make_source_info()
    info.server_name = name
    info.player_count = players
    info.max_players = 8
    return info


def test_probe_retries_only_failed_hosts():
    """首轮失败的服在第二轮重试；首轮成功的绝不再查一次。"""
    api = _fresh_probe_api(passes=2)
    calls: dict[tuple[str, int], int] = {}

    async def fake_ainfo(ip, **_kwargs):
        calls[ip] = calls.get(ip, 0) + 1
        # 第一轮全失败，第二轮全成功（用次数模拟）
        if calls[ip] == 1:
            raise TimeoutError("probe timeout")
        return _probe_info()

    ips = [("1.1.1.1", 27015), ("2.2.2.2", 27015)]
    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", AsyncMock(return_value=[])),
    ):
        results = asyncio.run(api.a2s_info_batch(ips, want_players=False, probe=True))

    assert calls == dict.fromkeys(ips, 2), f"每台应查 2 轮，实际 {calls}"
    assert all(info.max_players == 8 for info, _ in results)


def test_probe_online_host_queried_once_only():
    """首轮就成功的服不会被第二轮重复查询。"""
    api = _fresh_probe_api(passes=2)
    calls: dict[tuple[str, int], int] = {}

    async def fake_ainfo(ip, **_kwargs):
        calls[ip] = calls.get(ip, 0) + 1
        if ip[0] == "2.2.2.2":
            raise TimeoutError("probe timeout")
        return _probe_info()

    ips = [("1.1.1.1", 27015), ("2.2.2.2", 27015)]
    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", AsyncMock(return_value=[])),
    ):
        asyncio.run(api.a2s_info_batch(ips, want_players=False, probe=True))

    assert calls[("1.1.1.1", 27015)] == 1, "在线服只查一轮"
    assert calls[("2.2.2.2", 27015)] == 2, "失败服重试"


def test_probe_writes_negative_cache_and_skips_next_time():
    """两轮都失败的服进负缓存；下一次在 TTL 内直接跳过，不再打 UDP。"""
    api = _fresh_probe_api(passes=2, neg_ttl=60)
    dead = ("9.9.9.9", 27015)
    alive = ("1.1.1.1", 27015)
    dead_calls = 0

    async def fake_ainfo(ip, **_kwargs):
        nonlocal dead_calls
        if ip == dead:
            dead_calls += 1
            raise TimeoutError("dead server")
        return _probe_info()

    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", AsyncMock(return_value=[])),
    ):
        first = asyncio.run(
            api.a2s_info_batch([alive, dead], want_players=False, probe=True),
        )
        assert dead_calls == 2, "两轮都查（2 passes）"
        assert api._neg_cache, "失败服应写入负缓存"
        offline = [i for i, _ in first if i.max_players == 0]
        assert len(offline) == 1, "死服按离线返回"

        # 第二次：正缓存还在，死服走负缓存 —— 都不该再打 UDP
        before = dead_calls
        api._cache.clear()  # 只清正缓存，模拟 TTL 过期但负缓存仍有效
        asyncio.run(api.a2s_info_batch([alive, dead], want_players=False, probe=True))

    assert dead_calls == before, "负缓存命中时不应再查死服"


def test_probe_negative_cache_expires():
    api = _fresh_probe_api(passes=1, neg_ttl=0)
    dead = ("9.9.9.9", 27015)
    calls = 0

    async def fake_ainfo(_ip, **_kwargs):
        nonlocal calls
        calls += 1
        raise TimeoutError("dead")

    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", AsyncMock(return_value=[])),
    ):
        asyncio.run(api.a2s_info_batch([dead], want_players=False, probe=True))
        assert not api._neg_cache, "neg_ttl=0 时不该写负缓存"
        asyncio.run(api.a2s_info_batch([dead], want_players=False, probe=True))

    assert calls == 2, "没有负缓存时每次都要重查"


def test_probe_skips_players_for_empty_servers():
    """玩家列表只对 player_count > 0 的在线服查，空服不白跑一次 UDP。"""
    api = _fresh_probe_api(passes=1)
    ips = [("1.1.1.1", 27015), ("2.2.2.2", 27015)]

    async def fake_ainfo(ip, **_kwargs):
        # 1.1.1.1 有人，2.2.2.2 空服
        return _probe_info(players=3 if ip[0] == "1.1.1.1" else 0)

    aplayers_mock = AsyncMock(
        return_value=[a2s.Player(index=0, name="p1", score=1, duration=60.0)],
    )
    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", aplayers_mock),
    ):
        results = asyncio.run(api.a2s_info_batch(ips, want_players=True, probe=True))

    assert aplayers_mock.await_count == 1, "只对有人服查玩家"
    by_ip = {("1.1.1.1" if i == 0 else "2.2.2.2"): r for i, r in enumerate(results)}
    assert [p.name for p in by_ip["1.1.1.1"][1]] == ["p1"]
    assert by_ip["2.2.2.2"][1] == [], "空服玩家列表为空"


def test_probe_disabled_falls_back_to_plain_batch():
    """probe_timeout=0 时退回一次性查询（每台只查一次）。"""
    api = _fresh_probe_api(probe_timeout=0.0, passes=2)
    calls = 0

    async def fake_ainfo(_ip, **_kwargs):
        nonlocal calls
        calls += 1
        raise TimeoutError("dead")

    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", AsyncMock(return_value=[])),
    ):
        asyncio.run(
            api.a2s_info_batch([("9.9.9.9", 27015)], want_players=False, probe=True),
        )

    assert calls == 1, "probe_timeout=0 时只查一次，不重试"


def test_probe_result_order_matches_input_index():
    """probe 分支返回顺序与输入一致（steam_id 被覆盖成输入下标）。"""
    api = _fresh_probe_api(passes=1)
    ips = [("3.3.3.3", 27015), ("1.1.1.1", 27015), ("2.2.2.2", 27015)]

    with (
        patch.object(
            api_module.a2s,
            "ainfo",
            AsyncMock(side_effect=lambda ip, **_k: _probe_info(ip[0])),
        ),
        patch.object(api_module.a2s, "aplayers", AsyncMock(return_value=[])),
    ):
        results = asyncio.run(api.a2s_info_batch(ips, want_players=False, probe=True))

    assert [r[0].server_name for r in results] == ["3.3.3.3", "1.1.1.1", "2.2.2.2"]
    assert [r[0].steam_id for r in results] == [0, 1, 2]


def test_probe_dead_server_still_skips_aplayers():
    """探测失败（离线）时同样不该调 aplayers —— 与 ``_a2s_one`` 的既有约定一致。"""
    api = _fresh_probe_api(passes=2)

    async def fake_ainfo(_ip, **_kwargs):
        raise TimeoutError("dead")

    aplayers_mock = AsyncMock(return_value=[])
    with (
        patch.object(api_module.a2s, "ainfo", side_effect=fake_ainfo),
        patch.object(api_module.a2s, "aplayers", aplayers_mock),
    ):
        results = asyncio.run(
            api.a2s_info_batch([("9.9.9.9", 27015)], want_players=True, probe=True),
        )

    assert aplayers_mock.await_count == 0, "离线服不查玩家"
    assert results[0][0].max_players == 0
