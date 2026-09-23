"""Persistence for per-tag server group JSON files.

Each group lives at ``config.data_dir/<tag>.json``（默认经
``services.path_resolver`` 解析后的目录）with content
``{"<tag>": [{"id": "1", "ip": "host:port"}, ...]}``。

ID 稳定策略：

- 已存在的 ``{id, ip}`` 条目按 ``ip`` 去重保留原 id（不在原列表里的 ip 才会被
  加进去；SourceBans 抓取时按 ip 去重，避免重复出现）。
- 新条目 id = ``max(existing_ids, default=0) + 1``。
- 这样 ``云1`` 这类后缀指令引用稳定，SourceBans 刷新不会打乱顺序。

新加的单服 CRUD（``add_server`` / ``remove_server`` / ``update_server`` /
``list_servers``）让上层命令（``commands/server_mgmt.py``）可以不用再让用户
手动编辑 JSON 文件。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import aiofiles
import ujson as json

from ..config import config
from ..consts import NON_GROUP_FILENAMES
from ..http_helpers import split_maohao


def groups_dir() -> Path:
    """运行时权威的组文件目录（来自 ``config.data_dir``）。"""
    return config.data_dir


async def _ensure_dir() -> None:
    groups_dir().mkdir(parents=True, exist_ok=True)


def _coerce_ip(entry: object) -> str:
    """从任意条目里抽 ip 字符串（无法解析返回空串）。"""
    if isinstance(entry, str):
        return entry.strip()
    if isinstance(entry, dict):
        ip = entry.get("ip")
        if isinstance(ip, str) and ip.strip():
            return ip.strip()
    host = getattr(entry, "host", None)
    port = getattr(entry, "port", None)
    if host and port:
        return f"{host}:{port}"
    return ""


def _normalize_with_existing(
    servers: Iterable,
    existing: list[dict] | None = None,
) -> list[dict]:
    """稳定 ID 的归一化。

    - 已存在的 ``ip`` 沿用原 id 与原 ``host``/``port``（若有）；不重复添加。
    - 新 ip 接 ``max(existing_ids, default=0) + 1`` 续号。
    - 不传 ``existing`` 时退化为按出现顺序 1..N 重排（旧行为，SourceBans 刷新场景
      如果传入了新解析结果、希望完全覆盖时仍可用）。
    """
    seen_ip: set[str] = set()
    items: list[dict] = []
    if existing is not None:
        ip_to_entry: dict[str, dict] = {}
        max_id = 0
        for e in existing:
            ip = _coerce_ip(e)
            if not ip or ip in ip_to_entry:
                continue
            entry = dict(e) if isinstance(e, dict) else {"ip": ip}
            entry.setdefault("ip", ip)
            try:
                cur_id = int(entry.get("id", 0))
            except (TypeError, ValueError):
                cur_id = 0
            max_id = max(max_id, cur_id)
            ip_to_entry[ip] = entry
        for raw in servers or []:
            ip = _coerce_ip(raw)
            if not ip or ip in seen_ip:
                continue
            seen_ip.add(ip)
            existing_entry = ip_to_entry.pop(ip, None)
            if existing_entry is not None:
                items.append(existing_entry)
            else:
                max_id += 1
                host, port = split_maohao(ip)
                items.append(
                    {
                        "id": str(max_id),
                        "ip": ip,
                        "host": host,
                        "port": port,
                    },
                )
        return items

    # 无 existing：按顺序重排
    for raw in servers or []:
        ip = _coerce_ip(raw)
        if not ip or ip in seen_ip:
            continue
        seen_ip.add(ip)
        items.append(ip)
    return [{"id": str(i + 1), "ip": ip} for i, ip in enumerate(items)]


def _normalize(servers: Iterable) -> list[dict]:
    """旧版归一化（SourceBans 抓取场景：稳定 1..N 顺序）。"""
    return _normalize_with_existing(servers, existing=None)


async def set_group(tag: str, servers: Iterable) -> Path:
    """写入整组（SourceBans 刷新场景）。

    稳定 ID：已存在的 ip 沿用原 id，新增 ip 接 max+1。
    """
    await _ensure_dir()
    tag = str(tag).strip()
    existing = await get_group(tag)
    items = _normalize_with_existing(servers, existing=existing)
    content = json.dumps({tag: items}, ensure_ascii=False, indent=4)
    path = groups_dir() / f"{tag}.json"
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content + "\n")
    return path


async def get_group(tag: str) -> list[dict]:
    """读取 ``tag`` 的服务器列表；缺失返回 ``[]``。"""
    await _ensure_dir()
    path = groups_dir() / f"{str(tag).strip()}.json"
    if not path.is_file():
        return []
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "{}")
        if isinstance(data, dict):
            raw = data.get(str(tag), [])
            return raw if isinstance(raw, list) else []
    except Exception:
        return []
    return []


async def list_servers(tag: str) -> list[dict]:
    """等同 ``get_group``，仅语义化为 CRUD 接口的一部分。"""
    return await get_group(tag)


def _identifier_to_filter(identifier: str | int) -> tuple[str, int] | None:
    """把 ``id`` 或 ``ip`` 转成 ip 匹配键。

    返回 ``("id", N)`` 或 ``("ip", "host:port")``；无法解析返回 None。
    """
    if isinstance(identifier, int):
        return ("id", identifier)
    s = str(identifier).strip()
    if not s:
        return None
    if s.isdigit():
        return ("id", int(s))
    return ("ip", s)


async def add_server(tag: str, ip: str) -> dict:
    """新增单服；tag 不存在则自动建空组。

    Returns 新条目 ``{id, ip, host, port}``。若 ip 已存在，返回原条目。
    """
    tag = str(tag).strip()
    ip = str(ip).strip()
    if not tag or not ip:
        raise ValueError("add_server: tag 和 ip 都必须非空")

    await _ensure_dir()
    existing = await get_group(tag)
    # 已存在直接返回原条目
    for entry in existing:
        if entry.get("ip") == ip:
            return entry

    next_id = 0
    for e in existing:
        try:
            cur = int(e.get("id", 0))
        except (TypeError, ValueError):
            cur = 0
        next_id = max(next_id, cur)
    next_id += 1
    host, port = split_maohao(ip)
    new_entry: dict = {"id": str(next_id), "ip": ip, "host": host, "port": port}

    items = [*list(existing), new_entry]
    content = json.dumps({tag: items}, ensure_ascii=False, indent=4)
    path = groups_dir() / f"{tag}.json"
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content + "\n")
    return new_entry


async def remove_server(tag: str, identifier: str | int) -> bool:
    """删除单服。``identifier`` 可以是 id（int 或数字串）或 ip。

    找到并删除返回 True；tag 不存在或条目没找到返回 False。
    """
    tag = str(tag).strip()
    key = _identifier_to_filter(identifier)
    if key is None:
        return False

    existing = await get_group(tag)
    if not existing:
        return False

    kind, value = key
    new_items: list[dict] = []
    removed = False
    for entry in existing:
        if not removed and (
            (kind == "id" and str(entry.get("id", "")) == str(value))
            or (kind == "ip" and entry.get("ip") == value)
        ):
            removed = True
            continue
        new_items.append(entry)

    if not removed:
        return False

    path = groups_dir() / f"{tag}.json"
    if new_items:
        content = json.dumps({tag: new_items}, ensure_ascii=False, indent=4)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content + "\n")
    else:
        # 空组：删文件，避免遗留空壳
        if path.is_file():
            path.unlink()
    return True


async def update_server(
    tag: str,
    identifier: str | int,
    new_ip: str,
) -> dict | None:
    """修改单服 ip。返回更新后的条目；未找到返回 None。"""
    tag = str(tag).strip()
    new_ip = str(new_ip).strip()
    if not new_ip:
        raise ValueError("update_server: new_ip 不能为空")
    if split_maohao(new_ip)[1] == -1:
        raise ValueError(f"update_server: 无效的 ip {new_ip!r}")

    key = _identifier_to_filter(identifier)
    if key is None:
        return None

    existing = await get_group(tag)
    kind, value = key
    updated: dict | None = None
    new_items: list[dict] = []
    for entry in existing:
        match = (
            (kind == "id" and str(entry.get("id", "")) == str(value))
            or (kind == "ip" and entry.get("ip") == value)
        )
        if match and updated is None:
            host, port = split_maohao(new_ip)
            updated = {
                **entry,
                "ip": new_ip,
                "host": host,
                "port": port,
            }
            new_items.append(updated)
        else:
            new_items.append(entry)

    if updated is None:
        return None

    path = groups_dir() / f"{tag}.json"
    content = json.dumps({tag: new_items}, ensure_ascii=False, indent=4)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content + "\n")
    return updated


async def remove_group(tag: str) -> bool:
    """删除整组 JSON。返回是否原本存在。"""
    await _ensure_dir()
    path = groups_dir() / f"{str(tag).strip()}.json"
    if path.is_file():
        path.unlink()
        return True
    return False


async def list_groups() -> list[str]:
    """所有组名（文件名去掉 .json；收藏 / 通知状态 / sb_pages 等不算）。"""
    await _ensure_dir()
    names: list[str] = []
    for p in groups_dir().glob("*.json"):
        if p.is_file() and p.name not in NON_GROUP_FILENAMES:
            names.append(p.stem)
    names.sort()
    return names


async def export_all() -> dict[str, list[dict]]:
    """内存里导出所有组。"""
    await _ensure_dir()
    result: dict[str, list[dict]] = {}
    for name in await list_groups():
        result[name] = await get_group(name)
    return result


# 暴露给其他模块的常量
_PORT_RE = re.compile(r"^\d+$")
