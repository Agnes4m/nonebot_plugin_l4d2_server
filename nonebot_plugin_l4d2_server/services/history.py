"""A2S 历史持久化（SQLite）+ Wipe 检测。

每个订阅组的 A2S 巡检结果会落 ``<data_dir>/history.db``（Python 3.12+
自带 ``sqlite3``，零新依赖）。派生三种能力：

- 热力图查询：``heatmap(server, days=7) -> list[(weekday, hour, avg_count)]``
- Wipe 检测：``detect_wipe(server, current_map) -> str | None``，与上一次
  记录的 map 不一致时返回旧 map 名（即「重置前的章节」），配合
  ``favorites`` 推送给订阅者。
- 阈值智能通知：见 ``services/favorite.py`` 的 ``_maybe_threshold_alert``。
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Iterable

from nonebot.log import logger

from ..config import config

_DDL = """
CREATE TABLE IF NOT EXISTS a2s_history (
    timestamp   INTEGER NOT NULL,
    host        TEXT    NOT NULL,
    port        INTEGER NOT NULL,
    server_name TEXT,
    map_name    TEXT,
    player_count INTEGER NOT NULL,
    max_players  INTEGER NOT NULL,
    ping        INTEGER,
    PRIMARY KEY (host, port, timestamp)
);
CREATE INDEX IF NOT EXISTS idx_hp_ts
    ON a2s_history(host, port, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts
    ON a2s_history(timestamp DESC);
"""

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _db_path() -> Path:
    """``<data_dir>/history.db``；目录由 path_resolver 保证存在。"""
    return config.data_dir / "history.db"


def _conn_lazy() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        path = _db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(path), check_same_thread=False)
        _conn.executescript(_DDL)
        _conn.commit()
    return _conn


def record(
    *,
    host: str,
    port: int,
    server_name: str | None,
    map_name: str | None,
    player_count: int,
    max_players: int,
    ping: int | None,
    timestamp: int | None = None,
) -> None:
    """写一条历史记录。timestamp 默认 ``time.time()``。"""
    if timestamp is None:
        timestamp = int(time.time())
    with _lock:
        conn = _conn_lazy()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO a2s_history "
                "(timestamp, host, port, server_name, map_name, "
                "player_count, max_players, ping) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    timestamp, host, port, server_name, map_name,
                    player_count, max_players, ping,
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            logger.warning(f"[l4] 写历史失败 {host}:{port}: {exc}")


def latest_map(host: str, port: int) -> str | None:
    """上一次记录的 ``map_name``；无记录返回 None。"""
    with _lock:
        conn = _conn_lazy()
        row = conn.execute(
            "SELECT map_name FROM a2s_history "
            "WHERE host=? AND port=? "
            "ORDER BY timestamp DESC LIMIT 1",
            (host, port),
        ).fetchone()
    return row[0] if row else None


def detect_wipe(host: str, port: int, current_map: str | None) -> str | None:
    """地图变化检测：返回 ``(旧 map, 新 map)`` 字符串；未变化返回 None。

    返回的字符串形如 ``"c1m1_highway → c1m2_streets"``。
    """
    if not current_map:
        return None
    previous = latest_map(host, port)
    if not previous or previous == current_map:
        return None
    return f"{previous} → {current_map}"


def heatmap(
    host: str,
    port: int,
    days: int = 7,
) -> list[tuple[int, int, float, int]]:
    """返回 ``[(weekday 0-6, hour 0-23, avg_player_count, sample_count)]``。

    0 = 周一，6 = 周日。``sample_count`` 是该 (weekday, hour) 内的样本数，
    样本太少（<3）时 ``avg_player_count`` 也置 0 以避免误导。
    """
    cutoff = int(time.time()) - days * 86400
    with _lock:
        conn = _conn_lazy()
        rows = conn.execute(
            "SELECT timestamp, player_count FROM a2s_history "
            "WHERE host=? AND port=? AND timestamp>=?",
            (host, port, cutoff),
        ).fetchall()

    buckets: dict[tuple[int, int], list[int]] = {}
    for ts, pc in rows:
        lt = time.localtime(ts)
        key = (lt.tm_wday, lt.tm_hour)
        buckets.setdefault(key, []).append(pc)

    out: list[tuple[int, int, float, int]] = []
    for wd in range(7):
        for h in range(24):
            samples = buckets.get((wd, h), [])
            if len(samples) >= 3:
                avg = sum(samples) / len(samples)
            else:
                avg = 0.0
            out.append((wd, h, avg, len(samples)))
    return out


def purge_older_than(days: int) -> int:
    """删除 ``timestamp < now - days*86400`` 的记录；返回删除条数。"""
    cutoff = int(time.time()) - days * 86400
    with _lock:
        conn = _conn_lazy()
        cur = conn.execute(
            "DELETE FROM a2s_history WHERE timestamp<?", (cutoff,),
        )
        conn.commit()
        return cur.rowcount


def all_tracked_hosts() -> Iterable[tuple[str, int]]:
    """返回数据库里所有出现过的 (host, port)。"""
    with _lock:
        conn = _conn_lazy()
        rows = conn.execute(
            "SELECT DISTINCT host, port FROM a2s_history",
        ).fetchall()
    return [(r[0], r[1]) for r in rows]