import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher

from ..config import config

local_path_list = config.l4_local


local_path: list[Path] = []
for folder_path in local_path_list:
    path = Path(folder_path)

    if path.is_dir():
        for nextdir in path.iterdir():
            # 如果找到了名为left4dead2的目录,返回True
            if nextdir.name == "left4dead2" and nextdir.is_dir():
                local_path.append(nextdir)
        continue
logger.debug(f"本地服务器路径列表:{local_path}")


def sort_key(filename: str):
    # 提取文件名开头的数字（如果有）
    num_part = ""
    for char in filename:
        if char.isdigit():
            num_part += char
        elif num_part:  # 遇到非数字且已经有数字部分时停止
            break

    # 返回一个元组作为排序依据：(数字值, 整个文件名)
    # 使用正数表示升序，没有数字的用无穷大排在最后
    return (
        int(num_part) if num_part else float("inf"),
        filename,
    )


def get_vpk_files(local_path_index: int) -> list[str]:
    """获取指定索引的本地路径下的VPK文件列表"""
    try:
        supath = local_path[local_path_index] / "addons"
    except IndexError:
        logger.warning(
            "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
        )
        return []

    vpk_list: list[str] = []
    if supath.is_dir():
        for sudir in supath.iterdir():
            logger.debug(f"找到文件:{sudir}")
            if sudir.is_file() and sudir.name.endswith(".vpk"):
                vpk_list.append(sudir.name)

    vpk_list.sort(key=sort_key)
    return vpk_list


def validate_local_path() -> bool:
    """验证本地路径是否有效"""
    if not local_path:
        logger.warning(
            "未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径",
        )
        return False
    return True


async def process_map_change_or_delete(
    matcher: Matcher,
    args: str,
    is_delete: bool = False,
) -> Optional[Tuple[int, str]]:
    """处理地图修改或删除的通用逻辑"""
    args = args.strip()
    if args == "0":
        return None

    if not args:
        prompt = (
            "请输入要删除的地图序号"
            if is_delete
            else "请输入修改的地图序号和地图名称，以空格隔开，回复0取消"
        )
        await matcher.pause(prompt)
        return None

    if is_delete:
        if not args.isdigit():
            await matcher.pause("请输入要删除的地图序号")
        return (int(args), "")

    parts = args.split(" ", maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit():
        prompt = "请正确输入修改的地图序号和地图名称，以空格隔开，回复0取消"
        await matcher.pause(prompt) if not is_delete else await matcher.finish(prompt)
        return None

    return (int(parts[0]), parts[1])


async def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


async def format_text_to_html(text: str):
    html_parts = []
    paragraphs = re.split(r"\r?\n\r?\n", text.strip())

    for para in paragraphs:
        if not para.strip():
            continue

        title_match = re.match(r"^\s*~{\s*(.*?)\s*}~\s*$", para)
        if title_match:
            html_parts.append(
                f'<h2 class="adjustable-heading">{title_match.group(1)}</h2>',
            )
            continue

        if para.lstrip().startswith("- "):
            list_items = []
            for line in para.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    list_items.append(f"<li>{line[2:].strip()}</li>")
                elif line and list_items:
                    list_items[-1] = list_items[-1].replace(
                        "</li>",
                        f"<br>{line.strip()}</li>",
                    )
            html_parts.append(f'<ul>{"".join(list_items)}</ul>')
            continue

        processed_para = re.sub(
            r"\[url=([^\]]+)\]([^\[]+)\[/url\]",
            r'<a href="\1" target="_blank">\2</a>',
            para,
        )
        processed_para = " ".join(processed_para.split())
        processed_para = processed_para.replace("\n", "<br>")
        html_parts.append(f"<p>{processed_para}</p>")

    return "\n".join(html_parts)
