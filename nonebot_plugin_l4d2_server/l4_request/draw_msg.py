import asyncio

# from logging import log
import io
from pathlib import Path
from typing import List, Tuple

from nonebot.log import logger
from PIL import Image, ImageDraw, ImageFont

from ..config import config
from ..utils.api.models import NserverOut, OutServer
from ..utils.api.request import L4API


async def draw_one_ip(host: str, port: int, is_img: bool = config.l4_image):
    """输出单个ip"""
    try:
        ser_list = await L4API.a2s_info([(host, port)], is_player=True)
    except asyncio.exceptions.TimeoutError:
        return "服务器无响应"
    one_server = ser_list[0][0]
    one_player = ser_list[0][1]

    async def format_player_info(players: list) -> str:
        """格式化玩家信息
        Args:
            players: 玩家对象列表
        Returns:
            格式化后的玩家信息字符串
        """
        player_msg = ""
        if len(players):
            max_duration_len = max(
                [len(str(await convert_duration(i.duration))) for i in players],
            )
            max_score_len = max(len(str(i.score)) for i in players)

            for player in players:
                soc = "[{:>{}}]".format(player.score, max_score_len)
                chines_dur = await convert_duration(player.duration)
                dur = "{:^{}}".format(chines_dur, max_duration_len)
                name_leg = len(player.name)
                if name_leg > 2:
                    xing = ":)" * (name_leg - 2)
                    name = f"{player.name[0]}{xing}{player.name[-1]}"
                else:
                    name = player.name
                player_msg += f"{soc} | {dur} | {name} \n"
        else:
            player_msg = "服务器感觉很安静啊"
        return player_msg

    def build_server_message(server, player_info: str) -> str:
        """构建服务器信息消息
        Args:
            server: 服务器对象
            player_info: 格式化后的玩家信息字符串
        Returns:
            完整的服务器信息字符串
        """
        msg = f"""-{server.server_name}-
游戏: {server.folder}
地图: {server.map_name}
人数: {server.player_count}/{server.max_players}"""
        if server.ping is not None:
            msg += f"""
ping: {server.ping * 1000:.0f}ms
{player_info}"""
        if config.l4_show_ip:
            msg += f"""
connect {host}:{port}"""
        return msg

    def draw_text_on_image(
        text: str,
        font: ImageFont.FreeTypeFont,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:
        """在图片上绘制文本
        Args:
            text: 要绘制的文本
            font: PIL字体对象
            draw: PIL绘图对象
        Returns:
            包含绘制文本的PIL图片对象
        """
        try:
            # 分割文本为标题行和内容行
            lines = text.split("\n")
            if not lines:
                return Image.new("RGB", (600, 400), color=(73, 109, 137))

            title = lines[0]
            content = "\n".join(lines[1:]) if len(lines) > 1 else ""

            # 计算各部分文字尺寸
            title_bbox = font.getbbox(title)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]

            content_width = 0
            content_height = 0
            if content:
                content_lines = content.split("\n")
                line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
                content_height = len(content_lines) * line_height
                content_width = max(
                    font.getbbox(line)[2] - font.getbbox(line)[0]
                    for line in content_lines
                )

            # 计算图片尺寸
            margin = 20
            line_spacing = 5
            img_width = max(title_width, content_width) + 2 * margin
            content_lines_count = len(content.split("\n")) if content else 0
            img_height = max(
                title_height
                + content_height
                + (line_spacing + 1) * max(0, content_lines_count - 1)
                + 2 * margin,
                300,
            )

            # 加载背景图片
            bg_path = (
                Path(__file__).parent.parent / "l4_image" / "img" / "anne" / "back.png"
            )
            try:
                img = Image.open(bg_path)
                # 调整背景图尺寸
                img = img.resize((int(img_width), int(img_height)))
                logger.info(f"图片像素大小: {img.width}x{img.height}")
                draw = ImageDraw.Draw(img)

                title_x = (img_width - title_width) // 2
                title_y = margin
                draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255))

                if content:
                    content_x = margin
                    content_y = title_y + title_height + margin
                    draw.text(
                        (content_x, content_y),
                        content,
                        font=font,
                        fill=(255, 255, 255),
                        spacing=line_spacing,
                    )

                    return img
            except Exception as e:
                logger.error(f"加载背景图片失败: {e}")
                img = Image.new(
                    "RGB",
                    (int(img_width), int(img_height)),
                    color=(73, 109, 137),
                )
                draw = ImageDraw.Draw(img)
                draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255))
                if content:
                    draw.text(
                        (content_x, content_y),
                        content,
                        font=font,
                        fill=(255, 255, 255),
                        spacing=line_spacing,
                    )
                return img
        except Exception as e:
            logger.error(f"绘制图片时出错: {e}")
            error_img = Image.new("RGB", (600, 400), color=(255, 0, 0))
            error_draw = ImageDraw.Draw(error_img)
            error_draw.text((10, 10), "图片生成失败", fill=(255, 255, 255))
            return error_img

    player_info = await format_player_info(one_player)
    server_message = build_server_message(one_server, player_info)

    if is_img:
        # 加载字体
        font_path = Path(__file__).parent.parent / "data" / "font" / "loli.ttf"
        font = ImageFont.truetype(str(font_path), 18)
        draw = ImageDraw.Draw(Image.new("RGB", (600, 400), color=(73, 109, 137)))
        img = draw_text_on_image(server_message, font, draw)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()
    return server_message


async def get_much_server(server_json: List[NserverOut], command: str):
    out_server: List[OutServer] = []
    search_list: List[Tuple[str, int]] = []
    for i in server_json:
        search_list.append((i["host"], i["port"]))

    all_server = await L4API.a2s_info(search_list, is_player=True)

    for index, i in enumerate(all_server):
        out_server.append(
            {
                "server": i[0],  # type: ignore
                "player": i[1],
                "host": server_json[index]["host"],
                "port": server_json[index]["port"],
                "command": command,
                "id_": server_json[index]["id"],
            },
        )

    return out_server


async def convert_duration(duration: float) -> str:
    """Convert duration in seconds to human-readable string format (e.g. '1h 30m 15s')
    Args:
        duration: Duration in seconds
    Returns:
        Formatted time string
    """
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    time_str = ""
    if hours > 0:
        time_str += f"{int(hours)}h "
    if minutes > 0:
        time_str += f"{int(minutes)}m "
    time_str += f"{int(seconds)}s"
    return time_str
