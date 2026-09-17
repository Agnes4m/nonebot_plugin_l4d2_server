"""服务器远程控制命令。

每条服务器记录（JSON 里的一个对象）可以挂三条可选 shell 命令：

- ``cstop`` —— ``l4停止 <组> <id>`` 时执行（如 ``ssh root@ali 'systemctl stop anne'``）。
- ``crestart`` —— ``l4重启 <组> <id>`` 时执行。
- ``ccmd`` —— ``l4执行 <组> <id> <shell片段>`` 时执行；命令里的 ``{action}``
  会被替换为用户传入的片段（默认占位符）。

所有指令 SUPERUSER。执行前要求 ``l4确认`` 二步确认；执行结果与审计
日志写到 ``data_dir/audit.log``。
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path

from nonebot.adapters import Message
from nonebot.matcher import Matcher, current_event
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from ..services.errors import L4Error, L4InvalidInputError, L4NotFoundError

# 命令名（l4停止 / l4重启 / l4执行 / l4确认）
l4_stop = on_command(
    "l4停止", aliases={"l4_stop", "l4stop"}, permission=SUPERUSER,
)
l4_restart = on_command(
    "l4重启", aliases={"l4_restart", "l4restart"}, permission=SUPERUSER,
)
l4_runscript = on_command(
    "l4执行", aliases={"l4_runcmd", "l4runcmd"}, permission=SUPERUSER,
)
l4_confirm = on_command(
    "l4确认", aliases={"l4_confirm", "l4confirm"}, permission=SUPERUSER,
)

CONFIRM_WINDOW_SEC = 60  # 二次确认窗口：60 秒内有效
RUN_TIMEOUT_SEC = 60      # 单条命令超时

# 待确认操作：``(user_id, command_payload) -> expire_at``
_pending: dict[tuple[int, str], float] = {}


def _audit_path() -> Path:
    """审计日志路径：``<data_dir>/audit.log``。"""
    from ..config import config

    return config.data_dir / "audit.log"


def _audit(user_id: int, group_id: int, action: str, target: str,
           command: str, exit_code: int | None) -> None:
    """追加一行 JSON 到 ``audit.log``；失败不抛，避免审计写入影响主流程。"""
    line = (
        f"{datetime.now().isoformat(timespec='seconds')}\t"
        f"user={user_id}\tgroup={group_id}\t{action}\t{target}\t"
        f"exit={exit_code}\tcmd={command!r}\n"
    )
    try:
        path = _audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def _lookup_server(tag: str, identifier: str) -> tuple[str, dict]:
    """按组名 + id/ip 找服务器条目；返回 ``(key, entry)``。"""
    from ..registry import registry

    servers = registry.get(tag)
    if not servers:
        raise L4NotFoundError(f"组「{tag}」不存在或为空")
    ident = identifier.strip()
    for entry in servers:
        if str(entry.get("id")) == ident:
            return f"{tag}{entry.get('id')}", entry
    for entry in servers:
        if entry.get("ip") == ident:
            return f"{tag}{entry.get('id')}", entry
    raise L4NotFoundError(f"未找到 {tag} 中的 {identifier}")


def _command_for(entry: dict, action: str, extra: str = "") -> str:
    """根据 action 选 ``cstop / crestart / ccmd``，缺字段报错。"""
    if action == "stop":
        cmd = entry.get("cstop")
        label = "停止"
    elif action == "restart":
        cmd = entry.get("crestart")
        label = "重启"
    elif action == "run":
        cmd = entry.get("ccmd")
        label = "执行"
    else:
        raise L4InvalidInputError(f"未知 action：{action}")
    if not cmd or not isinstance(cmd, str):
        raise L4InvalidInputError(
            f"服务器 {entry.get('ip')} 未配置 c{action} 命令",
        )
    if action == "run" and extra:
        cmd = cmd.replace("{action}", extra)
    return label, cmd


async def _request_confirm(
    matcher: Matcher,
    user_id: int,
    payload: str,
    preview: str,
) -> None:
    """把待执行命令塞进 ``_pending``，回显预览让用户 ``l4确认``。"""
    expire_at = time.monotonic() + CONFIRM_WINDOW_SEC
    _pending[(user_id, payload)] = expire_at
    await matcher.send(
        f"即将执行：\n```\n{preview}\n```\n"
        f"60 秒内发送 ``l4确认`` 才会真正执行；"
        f"发 ``l4取消`` 可撤销。",
    )


def _cleanup_pending(now: float) -> None:
    """清掉过期 pending 项。"""
    stale = [k for k, exp in _pending.items() if exp <= now]
    for k in stale:
        _pending.pop(k, None)


async def _run(user_id: int, group_id: int, target: str, command: str,
               action: str) -> tuple[int, str, str]:
    """异步执行 shell 命令，返回 ``(exit_code, stdout, stderr)``。"""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        return -1, "", f"启动进程失败：{exc}"
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=RUN_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", f"命令超时（>{RUN_TIMEOUT_SEC}s）已 kill"
    exit_code = proc.returncode if proc.returncode is not None else -1
    _audit(
        user_id=user_id, group_id=group_id, action=action,
        target=target, command=command, exit_code=exit_code,
    )
    return exit_code, stdout.decode(errors="replace").strip(), \
        stderr.decode(errors="replace").strip()


async def _handle(
    matcher: Matcher,
    user_id: int,
    group_id: int,
    args: Message,
    action: str,
    extra: str = "",
) -> None:
    try:
        text = args.extract_plain_text().strip()
        parts = text.split(None, 2 if action == "run" else 1)
        if len(parts) < 2:
            raise L4InvalidInputError(
                {"stop": "用法：l4停止 <组名> <id或ip>",
                 "restart": "用法：l4重启 <组名> <id或ip>",
                 "run": "用法：l4执行 <组名> <id或ip> <命令片段>"}[action],
            )
        tag = parts[0]
        identifier = parts[1]
        if action == "run":
            extra = parts[2] if len(parts) > 2 else ""
        target, entry = _lookup_server(tag, identifier)
        label, cmd = _command_for(entry, action, extra=extra)
    except L4Error as exc:
        await UniMessage.text(str(exc)).finish()
        return

    payload = f"{user_id}|{target}|{action}|{extra}|{cmd}"
    await _request_confirm(
        matcher, user_id, payload,
        preview=f"操作：{label} {target}\n命令：{cmd}",
    )


@l4_stop.handle()
async def _(args: Message = CommandArg()) -> None:
    await _handle_stub(l4_stop, args, action="stop")


@l4_restart.handle()
async def _(args: Message = CommandArg()) -> None:
    await _handle_stub(l4_restart, args, action="restart")


@l4_runscript.handle()
async def _(args: Message = CommandArg()) -> None:
    await _handle_stub(l4_runscript, args, action="run")


async def _handle_stub(matcher: Matcher, args: Message, action: str) -> None:
    """从事件里取 user_id / group_id 后委派给 ``_handle``。"""
    event = current_event.get()
    user_id = int(getattr(event, "user_id", 0) or 0)
    group_id = int(getattr(event, "group_id", 0) or 0)
    await _handle(matcher, user_id, group_id, args, action)


@l4_confirm.handle()
async def _(args: Message = CommandArg()) -> None:
    """把待确认命令真的跑起来；不带参数 = 执行最近的 pending。"""
    text = args.extract_plain_text().strip()
    if text == "取消":
        _pending.clear()
        await UniMessage.text("✅ 已清空所有待执行操作").finish()
        return

    event = current_event.get()
    user_id = int(getattr(event, "user_id", 0) or 0)
    group_id = int(getattr(event, "group_id", 0) or 0)

    now = time.monotonic()
    _cleanup_pending(now)

    # 找这个用户最近的 pending（payload 包含 user_id 前缀）
    mine = [k for k in _pending if k[0] == user_id]
    if not mine:
        await UniMessage.text("❌ 没有待执行的操作；先发 ``l4停止 / l4重启 / l4执行``").finish()
        return

    # 取最早过期的（即最久的等待）
    payload_key = min(mine, key=lambda k: _pending[k])
    user_id_k, payload = payload_key
    _, target, action, extra, cmd = payload.split("|", 4)
    _pending.pop(payload_key, None)

    await UniMessage.text(f"▶ 正在执行 {action} {target} ...").send()
    exit_code, stdout, stderr = await _run(
        user_id, group_id, target, cmd, action,
    )

    lines = [
        f"✅ 完成：{action} {target}",
        f"退出码：{exit_code}",
    ]
    if stdout:
        lines.append("stdout：\n```\n" + stdout[:1500] + "\n```")
    if stderr:
        lines.append("stderr：\n```\n" + stderr[:1500] + "\n```")
    await UniMessage.text("\n".join(lines)).finish(reply=True)