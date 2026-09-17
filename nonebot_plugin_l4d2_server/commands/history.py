"""A2S 历史查询命令。

- ``l4热力图 [组] <id或ip> [天数]``：按周几 × 小时网格展示平均在线人数。
  数据来源 ``services.history`` 的 SQLite。
"""

from __future__ import annotations

from typing import Optional

from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command
from nonebot_plugin_alconna import UniMessage

from ..registry import registry
from ..services import history
from ..services.errors import L4Error, L4InvalidInputError, L4NotFoundError

l4_heatmap = on_command(
    "l4热力图", aliases={"l4_heatmap", "l4heatmap"}, permission=SUPERUSER,
)

_WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"]
_BLOCKS = "▁▂▃▄▅▆▇█"


def _bar(value: float, vmax: float, width: int = 8) -> str:
    """把数值映射成 8 个 unicode 块字符组成的条；max=0 时返回空白。"""
    if vmax <= 0 or value <= 0:
        return _BLOCKS[0] * width
    idx = min(int(value / vmax * (len(_BLOCKS) - 1) + 0.5), len(_BLOCKS) - 1)
    return _BLOCKS[idx] * width


def _format_heatmap(
    name: str,
    cells: list[tuple[int, int, float, int]],
) -> str:
    """``cells`` 长度固定 168（7*24）；输出 7 行 ASCII 条形。"""
    vmax = max((avg for _, _, avg, _ in cells if avg > 0), default=1.0)
    lines = [f"【{name}】最近 7 天 × 24 小时平均在线人数（max={vmax:.1f}）："]
    # 头部：0-23 时
    lines.append("      " + "".join(f"{h:>2d}" for h in range(0, 24, 2)))
    for wd in range(7):
        row_label = f"周{_WEEKDAY[wd]}"
        # 12 个 2h 单元格（0-23）
        bar = ""
        for h in range(0, 24, 2):
            # 用 2h 平均：[(h, h+1) 各取一行加权]
            avg = (cells[wd * 24 + h][2] + cells[wd * 24 + h + 1][2]) / 2
            bar += _bar(avg, vmax, width=2)
        # 把后缀补一行注释
        line = f"{row_label}  {bar}"
        lines.append(line)
    lines.append("")
    lines.append("样本数（避免误导：<3 样本的格子置 0）：")
    for wd in range(7):
        sample_count = sum(c[3] for c in cells[wd * 24:(wd + 1) * 24])
        if sample_count == 0:
            continue
        lines.append(f"  周{_WEEKDAY[wd]}: {sample_count}")
    return "\n".join(lines)


def _resolve_target(args: Message) -> tuple[str, str, int]:
    """返回 ``(组名, id/ip, 天数)``；参数不对抛 ``L4InvalidInputError``。"""
    text = args.extract_plain_text().strip()
    parts = text.split()
    if len(parts) < 2:
        raise L4InvalidInputError("用法：l4热力图 <组名> <id或ip> [天数]")
    tag = parts[0]
    identifier = parts[1]
    days = 7
    if len(parts) >= 3:
        try:
            days = int(parts[2])
        except ValueError as exc:
            raise L4InvalidInputError(f"无效的天数：{parts[2]}") from exc
        if days < 1 or days > 30:
            raise L4InvalidInputError("天数应在 1-30 之间")
    return tag, identifier, days


@l4_heatmap.handle()
async def _(args: Message = CommandArg()) -> None:
    try:
        tag, identifier, days = _resolve_target(args)
        servers = registry.get(tag)
        if not servers:
            raise L4NotFoundError(f"组「{tag}」不存在或为空")
        target_entry: Optional[dict] = None
        for entry in servers:
            if str(entry.get("id")) == identifier:
                target_entry = entry
                break
        if target_entry is None:
            for entry in servers:
                if entry.get("ip") == identifier:
                    target_entry = entry
                    break
        if target_entry is None:
            raise L4NotFoundError(f"未找到 {tag} 中的 {identifier}")

        host = target_entry.get("host") or ""
        port = target_entry.get("port")
        if not host or not port or port == -1:
            raise L4InvalidInputError(f"{tag}{target_entry.get('id')} 没有 host/port")

        cells = history.heatmap(host, int(port), days=days)
        display_name = f"{tag}{target_entry.get('id')} {target_entry.get('ip')}"
    except L4Error as exc:
        await UniMessage.text(str(exc)).finish()
        return

    await UniMessage.text(_format_heatmap(display_name, cells)).finish()