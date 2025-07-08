# from logging import log
import io
from pathlib import Path
from typing import List

from a2s import Player
from nonebot.log import logger
from PIL import Image, ImageDraw, ImageFont

from ..config import config
from ..l4_image.html_img import convert_duration
from ..message import Sm
from ..utils.api.models import NserverOut, OutServer
from ..utils.api.request import L4API


async def draw_one_ip(host: str, port: int, is_img: bool = config.l4_image):
    """输出单个ip"""
    ser_list = await L4API.a2s_info([(host, port)], is_player=True)
    if not ser_list or ser_list[0][0].max_players == 0:
        # except asyncio.exceptions.TimeoutError:
        return Sm.server_outtime
    one_server = ser_list[0][0]
    one_player = ser_list[0][1]

    async def format_player_info(player_list: list[Player]) -> str:
        player_msg = ""
        if len(player_list):
            max_duration_len = max(
                [len(str(await convert_duration(i.duration))) for i in player_list],
            )
            max_score_len = max(len(str(i.score)) for i in player_list)

            for player in player_list:
                soc = "[{:>{}}]".format(player.score, max_score_len)
                chines_dur = await convert_duration(player.duration)
                dur = "{:^{}}".format(chines_dur, max_duration_len)
                name = str(player.name).strip()
                player_msg += f"{soc} | {dur} | {name[:15]} \n"
        else:
            player_msg = "服务器感觉很安静啊\n"
        return player_msg

    def build_server_message(server, player_info: str) -> str:
        """构建服务器信息消息
        Args:
            server: 服务器对象
            player_info: 格式化后的玩家信息字符串
        Returns:
            完整的服务器信息字符串
        """
        logger.info(player_info)
        vac_status = "启用" if server.vac_enabled else "禁用"
        msg = f"""-{server.server_name}-
游戏: {server.folder}
地图: {server.map_name}
人数: {server.player_count} / {server.max_players}"""
        if server.ping is not None:
            msg += f"""
延迟: {server.ping * 1000:.0f} ms
VAC : {vac_status}\n
{player_info}"""
        if config.l4_show_ip:
            msg += f"""
connect {host}:{port}"""
        return msg

    def draw_text_on_image(
        text: str,
        font: ImageFont.FreeTypeFont,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:  # type: ignore # 明确返回类型
        """在图片上绘制文本
        Args:
            text: 要绘制的文本
            font: PIL字体对象
            draw: PIL绘图对象
        Returns:
            包含绘制文本的PIL图片对象
        """
        # try:
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
                font.getbbox(line)[2] - font.getbbox(line)[0] for line in content_lines
            )
            line_widths = [
                font.getbbox(line)[2] - font.getbbox(line)[0] for line in content_lines
            ]
            logger.info(line_widths)

        # 计算图片尺寸
        margin = 20
        line_spacing = 7
        img_width = max(title_width, content_width) + 2 * margin
        logger.info(content_width)
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
            img = img.resize((int(min(img_width, 800)), int(img_height)))
            logger.info(f"图片像素大小: {img.width}x{img.height}")
            draw = ImageDraw.Draw(img)

            title_x = (img_width - title_width) // 2
            title_y = margin
            draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255))

            if content:
                content_x = margin
                content_y = title_y + title_height + margin

                # 定义不同参数值的颜色（冒号后的内容）
                value_colors = {
                    "游戏: ": (200, 180, 255),  # 淡紫
                    "地图: ": (166, 202, 253),  # 淡蓝
                    "人数: ": (100, 255, 100),  # 绿色
                    "延迟: ": (100, 255, 100),  # 绿色
                    "类型: ": (180, 220, 255),  # 淡蓝
                    "密码: ": (255, 255, 255),  # 白色
                    # connect不修改，保持原逻辑
                }

                # 按行绘制内容
                current_y = content_y
                for line in content_lines:
                    # 检查是否是参数行
                    colored = False
                    for prefix, color in value_colors.items():
                        if line.startswith(prefix):
                            # 绘制完整参数名（白色）
                            prefix_part = prefix
                            prefix_width = (
                                font.getbbox(prefix_part)[2]
                                - font.getbbox(prefix_part)[0]
                            )
                            draw.text(
                                (content_x, current_y),
                                prefix_part,
                                font=font,
                                fill=(255, 255, 255),
                            )

                            # 绘制参数值（带颜色）
                            value_part = line[len(prefix) :].strip()
                            draw.text(
                                (content_x + prefix_width, current_y),
                                value_part,
                                font=font,
                                fill=color,
                            )

                            colored = True
                            break
                    # 特殊处理VAC行
                    if not colored and line.startswith("VAC :"):
                        prefix = "VAC : "
                        prefix_width = font.getbbox(prefix)[2] - font.getbbox(prefix)[0]
                        draw.text(
                            (content_x, current_y),
                            prefix,
                            font=font,
                            fill=(255, 255, 255),
                        )

                        value_part = line[len(prefix) :].strip()
                        vac_color = (
                            (70, 209, 110) if value_part == "启用" else (255, 90, 90)
                        )  # 启用绿/禁用红
                        draw.text(
                            (content_x + prefix_width, current_y),
                            value_part,
                            font=font,
                            fill=vac_color,
                        )

                        colored = True

                    # 普通行（玩家信息）和connect保持原样
                    if not colored:
                        draw.text(
                            (content_x, current_y),
                            line,
                            font=font,
                            fill=(255, 255, 255),
                        )

                    current_y += line_height + line_spacing

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


async def get_much_server(
    server_json: List[NserverOut],
    command: str,
) -> List[OutServer]:
    out_server: List[OutServer] = []
    search_list = [(s["host"], s["port"]) for s in server_json]

    all_server = await L4API.a2s_info(search_list, is_player=True)

    for (server, player), srv_json in zip(all_server, server_json):
        out_server.append(
            OutServer(
                server=server,
                player=player,
                host=srv_json["host"],
                port=srv_json["port"],
                command=command,
                id_=srv_json["id"],
            ),
        )

    return out_server
