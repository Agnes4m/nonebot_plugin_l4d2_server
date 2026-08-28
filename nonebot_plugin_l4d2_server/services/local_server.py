"""Local L4D2 server: map listing / archive extraction / rename / delete. + ``server/local/utils.py`` (excluding
workshop download, which lives in ``services/workshop.py``).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from nonebot.log import logger
from pyunpack import Archive

from ..config import config
from ..http_helpers import list_vpk, save_url_to_file

SUPPORTED_EXTENSIONS = (".zip", ".7z", ".rar")

_local_path_cache: list[Path] | None = None


def _get_local_paths() -> list[Path]:
    """Resolve ``config.l4_local`` entries to their ``left4dead2`` subdirs."""
    global _local_path_cache
    if _local_path_cache is not None:
        return _local_path_cache

    paths: list[Path] = []
    for entry in config.l4_local:
        path = Path(entry)
        if path.is_dir():
            for sub in path.iterdir():
                if sub.name == "left4dead2" and sub.is_dir():
                    paths.append(sub)
    _local_path_cache = paths
    logger.debug(f"本地服务器路径列表: {_local_path_cache}")
    return _local_path_cache


def _sort_key(name: str) -> tuple[int | float, str]:
    """Numeric prefix sort: '1foo.vpk' before '10foo.vpk'."""
    num = ""
    for char in name:
        if char.isdigit():
            num += char
        elif num:
            break
    return (int(num) if num else float("inf"), name)


def list_vpks(server_index: int) -> list[str]:
    """VPK files under the given server index's ``addons`` dir."""
    local_paths = _get_local_paths()
    try:
        addons = local_paths[server_index] / "addons"
    except IndexError:
        logger.warning("本地服务器路径无效")
        return []

    if not addons.is_dir():
        return []
    return sorted(
        (p.name for p in addons.iterdir() if p.is_file() and p.name.endswith(".vpk")),
        key=_sort_key,
    )


def has_local_paths() -> bool:
    return bool(_get_local_paths())


def addons_dir(server_index: int) -> Path | None:
    local_paths = _get_local_paths()
    try:
        addons = local_paths[server_index] / "addons"
    except IndexError:
        return None
    return addons if addons.is_dir() else None


# ---------- archive extraction ----------


def _unzip(download: Path) -> None:
    """Extract zip file, falling back to GBK decoding for Chinese filenames."""
    with zipfile.ZipFile(download, "r") as zf:
        for name, member in list(zf.NameToInfo.items()):
            try:
                real = name.encode("cp437").decode("gbk")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if real != name:
                member.filename = real
                del zf.NameToInfo[name]
                zf.NameToInfo[real] = member
        zf.extractall(download.parent)
    download.unlink()


def _un7z(download: Path) -> None:
    Archive(str(download)).extractall(str(download.parent))
    download.unlink()


_UNPACKERS = {
    ".zip": _unzip,
    ".7z": _un7z,
    ".rar": lambda p: (Archive(str(p)).extractall(str(p.parent)) or p.unlink(),),
}


def extract_archive(download: Path, name: str) -> str | None:
    """Extract the archive in-place. Returns status message, ``None`` if unsupported."""
    if name.endswith(".vpk"):
        return "vpk文件已下载"

    ext = next((e for e in SUPPORTED_EXTENSIONS if name.endswith(e)), None)
    if ext is None:
        raise ValueError(f"不支持的文件: {name}")
    unpack = _UNPACKERS[ext]
    unpack(download)
    return f"{ext[1:]}文件已下载,正在解压"


async def download_and_extract(
    addons: Path,
    name: str,
    url: str,
) -> list[str] | None:
    """Download an archive, extract it, and return the new VPK filenames."""
    before = set(list_vpk(addons))
    downloaded = addons / name
    if await save_url_to_file(url, downloaded) is None:
        return None
    try:
        msg = extract_archive(downloaded, name)
        logger.info(msg)
    except Exception:
        logger.exception("解压失败")
        return None
    after = set(list_vpk(addons))
    return sorted(after - before)


def list_vpk_files(addons: Path) -> list[str]:
    return sorted(
        (p.name for p in addons.iterdir() if p.is_file() and p.name.endswith(".vpk")),
        key=_sort_key,
    )


# ---------- rename / delete ----------


async def rename_vpk(addons: Path, old: str, new: str) -> bool:
    if not new.endswith(".vpk"):
        new += ".vpk"
    src = addons / old
    dst = addons / new
    try:
        if not src.exists():
            logger.error(f"文件 {old} 不存在")
            return False
        src.rename(dst)
        logger.info(f"文件 {old} 已重命名为 {new}")
    except PermissionError:
        logger.error(f"没有权限重命名 {old}")
        return False
    except Exception as exc:
        logger.error(f"重命名 {old} 失败: {exc}")
        return False
    else:
        return True


async def delete_vpk(addons: Path, name: str) -> bool:
    target = addons / name
    try:
        if not target.exists():
            logger.error(f"文件 {name} 不存在")
            return False
        target.unlink()
        logger.info(f"文件 {name} 已删除")
    except PermissionError:
        logger.error(f"没有权限删除 {name}")
        return False
    except Exception as exc:
        logger.error(f"删除 {name} 失败: {exc}")
        return False
    else:
        return True
