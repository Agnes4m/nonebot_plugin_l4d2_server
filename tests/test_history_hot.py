"""历史巡检「热服加密采样」的测试。

覆盖两层：

- ``services/history.recent_active_hosts`` 的筛选语义（只挑「最近有人且在线」
  的服，窗口 <=0 关闭，窗口外样本不算，同服去重）。
- ``services/history_hot.register_hot_job`` 的注册行为（两个配置任一为 0 就
  不注册；正常配置会挂上 interval 任务且周期/窗口符合预期）。

和其它测试一样手工构造包上下文，不执行插件 ``__init__.py``。
"""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

INNER_DIR = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"


def _pkg(name: str, path: Path) -> None:
    if name not in sys.modules:
        mod = ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod


_pkg("nonebot_plugin_l4d2_server", INNER_DIR)
_pkg("nonebot_plugin_l4d2_server.services", INNER_DIR / "services")
history = importlib.import_module("nonebot_plugin_l4d2_server.services.history")
history_hot = importlib.import_module("nonebot_plugin_l4d2_server.services.history_hot")


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """把 ``history`` 的数据库指到临时目录，并重置模块级单连接。"""
    monkeypatch.setattr(history, "config", SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(history, "_conn", None)
    yield tmp_path
    conn = history._conn
    if conn is not None:
        conn.close()
    history._conn = None


def _insert(host: str, port: int, *, pc: int, mp: int, ago: int = 0) -> None:
    history.record(
        host=host,
        port=port,
        server_name="srv",
        map_name="c1m1",
        player_count=pc,
        max_players=mp,
        ping=10,
        timestamp=int(time.time()) - ago,
    )


class _FakeScheduler:
    def __init__(self) -> None:
        self.jobs: list[dict] = []

    def add_job(self, func, trigger, **kwargs) -> None:
        self.jobs.append({"func": func, "trigger": trigger, **kwargs})


def _cfg(**overrides):
    base = {
        "l4_history_hot_interval": 300,
        "l4_history_hot_window": 7200,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


# ---------- recent_active_hosts ----------


@pytest.mark.usefixtures("tmp_db")
def test_recent_active_hosts_filters_by_player_count():
    """离线（mp=0）与空服（pc=0）都不算热服。"""
    _insert("1.1.1.1", 27015, pc=6, mp=8)
    _insert("2.2.2.2", 27015, pc=0, mp=8)
    _insert("3.3.3.3", 27015, pc=0, mp=0)
    assert history.recent_active_hosts(7200) == [("1.1.1.1", 27015)]


@pytest.mark.usefixtures("tmp_db")
def test_recent_active_hosts_respects_window():
    """窗口外的历史样本不算热服。"""
    _insert("1.1.1.1", 27015, pc=6, mp=8, ago=60_000)
    assert history.recent_active_hosts(7200) == []
    assert history.recent_active_hosts(86_400) == [("1.1.1.1", 27015)]


@pytest.mark.usefixtures("tmp_db")
def test_recent_active_hosts_disabled_when_window_zero():
    """窗口 0 表示关闭，直接返回空表、也不报错。"""
    _insert("1.1.1.1", 27015, pc=6, mp=8)
    assert history.recent_active_hosts(0) == []


@pytest.mark.usefixtures("tmp_db")
def test_recent_active_hosts_dedupes():
    """同一台服多条记录只出现一次。"""
    _insert("1.1.1.1", 27015, pc=6, mp=8)
    _insert("1.1.1.1", 27015, pc=3, mp=8, ago=30)
    assert history.recent_active_hosts(7200) == [("1.1.1.1", 27015)]


# ---------- register_hot_job ----------


@pytest.mark.parametrize(
    "overrides",
    [
        {"l4_history_hot_interval": 0},
        {"l4_history_hot_window": 0},
        {"l4_history_hot_interval": 0, "l4_history_hot_window": 0},
    ],
)
def test_register_hot_job_disabled(overrides):
    """两个配置任一为 0 就不注册任务，返回 False。"""
    sched = _FakeScheduler()
    assert history_hot.register_hot_job(sched, _cfg(**overrides)) is False
    assert sched.jobs == []


def test_register_hot_job_creates_interval_job():
    """正常配置会挂上 interval 任务，id / 周期 / 窗口都对。"""
    sched = _FakeScheduler()
    assert history_hot.register_hot_job(sched, _cfg()) is True
    assert len(sched.jobs) == 1
    job = sched.jobs[0]
    assert job["trigger"] == "interval"
    assert job["seconds"] == 300
    assert job["id"] == history_hot.HOT_JOB_ID


def test_hot_job_settings_reads_config():
    """``hot_job_settings`` 是纯函数，方便单元测。"""
    assert history_hot.hot_job_settings(_cfg()) == (300, 7200)
    assert history_hot.hot_job_settings(_cfg(l4_history_hot_interval=0)) is None
    assert history_hot.hot_job_settings(_cfg(l4_history_hot_window=0)) is None


# ---------- record_hot_servers ----------


@pytest.mark.usefixtures("tmp_db")
def test_record_hot_servers_skips_hosts_not_in_registry(monkeypatch):
    """历史里有、但已经不在任何组里的服不会被采样。"""
    _insert("1.1.1.1", 27015, pc=6, mp=8)  # 在 registry
    _insert("9.9.9.9", 27015, pc=6, mp=8)  # 已从组里删掉

    queried: list[list[tuple[str, int]]] = []

    class _FakeL4API:
        @staticmethod
        async def a2s_info_batch(ips, want_players=True, probe=False):  # noqa: ARG004
            queried.append(list(ips))
            return [(SimpleNamespace(player_count=1, max_players=8), []) for _ in ips]

    fake_api = ModuleType("nonebot_plugin_l4d2_server.api")
    fake_api.L4API = _FakeL4API
    fake_registry_mod = ModuleType("nonebot_plugin_l4d2_server.registry")
    fake_registry_mod.registry = SimpleNamespace(
        group_names=["云"],
        get=lambda _tag: [{"host": "1.1.1.1", "port": 27015}],
    )
    monkeypatch.setitem(sys.modules, "nonebot_plugin_l4d2_server.api", fake_api)
    monkeypatch.setitem(
        sys.modules,
        "nonebot_plugin_l4d2_server.registry",
        fake_registry_mod,
    )

    import asyncio

    assert asyncio.run(history_hot.record_hot_servers(7200)) == 1
    assert queried == [[("1.1.1.1", 27015)]]


@pytest.mark.usefixtures("tmp_db")
def test_record_hot_servers_no_hot_hosts(monkeypatch):
    """没有热服时直接返回 0，不发 A2S 请求。"""
    _insert("1.1.1.1", 27015, pc=0, mp=8)  # 空服，不算热

    class _FakeL4API:
        @staticmethod
        async def a2s_info_batch(ips, want_players=True, probe=False):  # noqa: ARG004
            raise AssertionError("不该发请求")

    fake_api = ModuleType("nonebot_plugin_l4d2_server.api")
    fake_api.L4API = _FakeL4API
    fake_registry_mod = ModuleType("nonebot_plugin_l4d2_server.registry")
    fake_registry_mod.registry = SimpleNamespace(
        group_names=["云"],
        get=lambda _tag: [{"host": "1.1.1.1", "port": 27015}],
    )
    monkeypatch.setitem(sys.modules, "nonebot_plugin_l4d2_server.api", fake_api)
    monkeypatch.setitem(
        sys.modules,
        "nonebot_plugin_l4d2_server.registry",
        fake_registry_mod,
    )

    import asyncio

    assert asyncio.run(history_hot.record_hot_servers(7200)) == 0
