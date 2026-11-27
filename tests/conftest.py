"""Pytest configuration.

Initialises a minimal nonebot runtime so the inner package's
``config.get_plugin_config(...)`` call works during test collection
(imports of the inner modules run before fixtures).

同时注册一个轻量的耗时记录器：每个用例跑完在日志里打一行耗时（含 setup /
call / teardown 三段），会话结束时再打一张最慢用例排行榜。
``--no-timing`` 可以关掉逐条输出，排行榜仍会打印。
"""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path

# Make the inner package importable as a top-level package so ``import registry``
# and ``from nonebot_plugin_l4d2_server.api.l4d2 import L4D2Api`` both work.
INNER = Path(__file__).parent.parent / "nonebot_plugin_l4d2_server"
sys.path.insert(0, str(INNER))

logger = logging.getLogger("l4.pytest.timing")

# 慢用例阈值（秒）：超过就升级到 WARNING，一眼看到拖慢套件的用例。
SLOW_CASE_SECONDS = 0.5
# 会话结束时打印的排行榜长度。
TOP_SLOWEST = 10

# nodeid -> {phase: 秒}
_phases: dict[str, dict[str, float]] = {}
# (总秒数, nodeid)
_timings: list[tuple[float, str]] = []
# ``--no-timing`` 状态；由 pytest_configure 写入，logreport 只有 report 可用。
_per_case_logs_enabled = True


def _ensure_nonebot() -> None:
    """Initialise nonebot with an empty env if not already up."""
    if "nonebot" not in sys.modules:
        return
    import nonebot  # type: ignore[import-not-found]
    from nonebot import get_driver  # type: ignore[import-not-found]

    try:
        get_driver()
    except ValueError:
        nonebot.init(env=types.SimpleNamespace(), _env_file=None)


# Run at import time (before any test collection).
_ensure_nonebot()
logging.getLogger("nonebot").setLevel(logging.CRITICAL)


def pytest_addoption(parser):
    """加 ``--no-timing`` 开关，嫌日志吵时可以关掉逐条输出。"""
    parser.addoption(
        "--no-timing",
        action="store_true",
        default=False,
        help="不输出每个用例的耗时日志（会话结束的排行榜仍会打印）",
    )


def pytest_configure(config):
    """Reset driver config so sub-tests with patched paths still work."""
    global _per_case_logs_enabled  # noqa: PLW0603
    _per_case_logs_enabled = not bool(config.getoption("--no-timing", default=False))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


def pytest_runtest_logreport(report):
    """累积 setup / call / teardown 三段耗时，在 teardown 结束时汇总输出。"""
    nodeid = report.nodeid
    phases = _phases.setdefault(nodeid, {})
    # 同一 phase 可能有多条 report（如 setup 失败后 call 也会记一条），累加。
    phases[report.when] = phases.get(report.when, 0.0) + float(report.duration)

    if report.when != "teardown":
        return

    _phases.pop(nodeid, None)
    total = sum(phases.values())
    _timings.append((total, nodeid))

    if not _per_case_logs_enabled:
        return

    detail = " ".join(f"{k[:4]}={v * 1000:.1f}ms" for k, v in phases.items())
    level = logging.WARNING if total >= SLOW_CASE_SECONDS else logging.INFO
    logger.log(level, f"[timing] {total * 1000:8.1f}ms  {nodeid}  ({detail})")


def pytest_terminal_summary(terminalreporter):
    """会话结束：打印总耗时与最慢的若干个用例。"""
    if not _timings:
        return
    total = sum(t for t, _ in _timings)
    terminalreporter.write_sep("-", "l4 test timings")
    terminalreporter.write_line(
        f"{len(_timings)} cases, cumulative call time {total:.2f}s",
    )
    for elapsed, nodeid in sorted(_timings, reverse=True)[:TOP_SLOWEST]:
        terminalreporter.write_line(f"{elapsed * 1000:8.1f}ms  {nodeid}")
