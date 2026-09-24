"""tj / zl / kl 筛选的回归测试（主要是 tj 从服务器名解析特感数量）。

和其它测试文件一样手工构造包上下文：``services`` / ``render`` 包不执行
``__init__.py``，只加载 ``services/filter.py`` 需要的模块。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import a2s
import pytest

INNER_DIR = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"


def _pkg(name: str, path: Path) -> None:
    """只登记包路径、不执行 ``__init__.py``；已存在就复用。"""
    if name not in sys.modules:
        mod = ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod


_pkg("nonebot_plugin_l4d2_server", INNER_DIR)
_pkg("nonebot_plugin_l4d2_server.services", INNER_DIR / "services")
_pkg("nonebot_plugin_l4d2_server.render", INNER_DIR / "render")
filter_mod = importlib.import_module("nonebot_plugin_l4d2_server.services.filter")


def _info(name: str) -> a2s.SourceInfo:
    return a2s.SourceInfo(
        protocol=17,
        server_name=name,
        map_name="c2m1_highway",
        folder="left4dead2",
        game="L4D2",
        app_id=550,
        player_count=4,
        max_players=8,
        bot_count=0,
        server_type="d",
        platform="l",
        password_protected=False,
        vac_enabled=True,
        version="1.0",
        edf=0,
        ping=0.03,
    )


def _players(*scores: int) -> list[a2s.Player]:
    return [
        a2s.Player(index=i, name=f"p{i}", score=s, duration=60.0)
        for i, s in enumerate(scores)
    ]


@pytest.mark.parametrize(
    ("name", "count"),
    [
        ("Anne云服#57[普通药役][缺人][无MOD][8特20秒]", 8),
        ("Anne云服#17[HT训练][2特0秒]", 2),
        ("Anne云服#9[普通药役][12特16秒]", 12),
        ("[8特20秒]普通药役", 8),  # 旧格式：特感标签在第一个方括号
        ("Anne云服#5[普通药役][药役 6 特]", 6),  # 方括号里不在开头也能认出
        ("Anne云服#1[普通药役]", None),
        ("Anne云服#3[Not0721战役Solo]", None),  # 有数字但不是「N特」
        ("Anne云服#8 普通药役 8特", None),  # 不在方括号里不算
    ],
)
def test_si_count_scans_every_bracket(name, count):
    assert filter_mod._si_count(name) == count


def test_tj_matches_when_top_scores_exceed_threshold():
    """特感数 × 50 < 前 4 名分数和 才算 tj；阈值来自任意方括号里的「N特」。"""
    server = _info("Anne云服#57[普通药役][缺人][无MOD][8特20秒]")
    assert filter_mod._is_tj_server(server, _players(150, 150, 101), ["普通药役"])
    assert not filter_mod._is_tj_server(
        server,
        _players(100, 100, 100, 100),
        ["普通药役"],
    )


def test_tj_rejects_other_modes_and_servers_without_si_tag():
    lots = _players(500, 500, 500, 500)
    assert not filter_mod._is_tj_server(
        _info("Anne云服#17[HT训练][2特0秒]"),
        lots,
        ["普通药役"],
    )
    assert not filter_mod._is_tj_server(
        _info("Anne云服#1[普通药役]"),
        lots,
        ["普通药役"],
    )
