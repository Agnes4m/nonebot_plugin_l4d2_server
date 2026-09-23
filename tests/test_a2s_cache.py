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
import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, patch

INNER_DIR = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# 构造一个空的 nonebot_plugin_l4d2_server 包，避免子模块导入时找不到包。
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
            try:
                delattr(self.obj, self.attr)
            except AttributeError:
                pass
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
        expire_at, value = api._cache[key]
        api._cache[key] = (time.monotonic() - 1, value)

        asyncio.run(api.a2s_info_batch(ips))
        assert ainfo_mock.await_count == 2, "TTL 过期应重新走网络"


def test_batch_orders_results_by_steam_id():
    """``a2s_info_batch`` 按 steam_id 升序返回，与输入 IP 顺序无关。

    steam_id 是 ``_a2s_one`` 里 ``server.steam_id = index``（enumerate
    index）写入的，不依赖服务端返回。
    """
    api = _fresh_api()

    async def fake_ainfo(ip, **kwargs):
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
