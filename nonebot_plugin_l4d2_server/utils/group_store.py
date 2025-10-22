# nonebot_plugin_l4d2_server/utils/group_store.py
from __future__ import annotations
from pathlib import Path
import aiofiles
import ujson as json

from ..config import config

# 每个组独立文件目录：data/L4D2/l4d2/<tag>.json
GROUPS_DIR = Path(config.l4_path) / "l4d2"

async def _ensure_dir():
    GROUPS_DIR.mkdir(parents=True, exist_ok=True)

def _normalize(servers) -> list[dict]:
    """支持对象(host/port)、{'ip': 'h:p'}、或 'h:p'；去重保序，id 从 1 开始（字符串）。"""
    seen, ips = set(), []
    for s in servers or []:
        ip = ""
        if isinstance(s, str):
            ip = s.strip()
        elif isinstance(s, dict) and "ip" in s:
            ip = str(s["ip"]).strip()
        else:
            host = getattr(s, "host", None)
            port = getattr(s, "port", None)
            if host is not None and port is not None:
                ip = f"{host}:{port}"
        if ip and ip not in seen:
            seen.add(ip)
            ips.append(ip)
    return [{"id": str(i + 1), "ip": ip} for i, ip in enumerate(ips)]

async def set_group(tag: str, servers) -> Path:
    """写入 data/L4D2/l4d2/<tag>.json ，内容为 { "<tag>": [ {id,ip}, ... ] }"""
    await _ensure_dir()
    tag = str(tag).strip()
    items = _normalize(servers)
    content = json.dumps({tag: items}, ensure_ascii=False, indent=4)
    path = GROUPS_DIR / f"{tag}.json"
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content + "\n")
    return path

async def get_group(tag: str) -> list[dict]:
    """读取单组文件，返回 [ {id,ip}, ... ]；不存在则返回空列表。"""
    await _ensure_dir()
    path = GROUPS_DIR / f"{str(tag).strip()}.json"
    if not path.is_file():
        return []
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    try:
        data = json.loads(text or "{}")
        return data.get(str(tag), [])
    except Exception:
        return []

async def remove_group(tag: str) -> bool:
    """删除单组文件。"""
    await _ensure_dir()
    path = GROUPS_DIR / f"{str(tag).strip()}.json"
    if path.is_file():
        path.unlink()
        return True
    return False

async def list_groups() -> list[str]:
    """列出现有组名（按文件名）。"""
    await _ensure_dir()
    names = []
    for p in GROUPS_DIR.glob("*.json"):
        if p.is_file():
            names.append(p.stem)
    names.sort()
    return names

async def export_all() -> dict:
    """读取目录下所有组，组合成 {tag: [..]} 的字典（仅用于导出，不落盘）。"""
    await _ensure_dir()
    result = {}
    for name in await list_groups():
        result[name] = await get_group(name)
    return result
