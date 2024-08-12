import asyncio
import hashlib
import io
import os
import random
from pathlib import Path

import httpx
from nonebot.log import logger
from PIL import Image, ImageDraw
from PIL.Image import Image as ImageS

from ..config import DATAOUT

TEXT_PATH = Path(__file__).parent


async def download_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url, timeout=20)
                resp.raise_for_status()
                if True:
                    return resp.content
            except Exception as e:
                logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                await asyncio.sleep(3)

    raise Exception(f"{url} 下载失败!")


async def download_head(user_id: str) -> bytes:
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
    data = await download_url(url)
    if (
        hashlib.md5(data).hexdigest() == "acef72340ac0e914090bd35799f5594e"
    ):  # noqa: S324
        url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=100"
        data = await download_url(url)
    return data


def square_to_circle(im: ImageS):
    """im是正方形,变圆形"""
    size = im.size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, *size), fill=255)
    # 将遮罩层应用到图像上
    im.putalpha(mask)
    return im


async def get_head_by_user_id_and_save(user_id: str):
    """qq转头像"""
    user_id = str(user_id)

    user_head_path = DATAOUT / user_id / "HEAD.png"
    default_header_path = TEXT_PATH / "header"
    default_head_path = TEXT_PATH / "head"
    default_header = default_header_path / random.choice(
        os.listdir(default_header_path),
    )
    default_head = default_head_path / random.choice(os.listdir(default_head_path))
    # im头像 im2头像框 im3合成
    if user_head_path.exists():
        logger.info("使用本地头像")
        im = Image.open(user_head_path).resize((280, 280)).convert("RGBA")
    else:
        if user_id == "1145149191810":
            logger.info("使用默认头像")
            im = Image.open(default_header).resize((280, 280)).convert("RGBA")
        else:
            try:
                logger.info("正在下载头像")
                image_bytes = await download_head(user_id)
                im = (
                    Image.open(io.BytesIO(image_bytes))
                    .resize((280, 280))
                    .convert("RGBA")
                )
                if not (DATAOUT / user_id).exists():  # 用户文件夹不存在
                    (DATAOUT / user_id).mkdir(parents=True, exist_ok=True)
                im.save(user_head_path, "PNG")
            except Exception:
                logger.error("获取失败")
                return None
    im2 = Image.open(default_head).resize((450, 450)).convert("RGBA")
    im3 = Image.new("RGBA", im2.size, (255, 255, 255, 0))
    _, _, _, a1 = im.split()
    _, _, _, a2 = im2.split()
    im = square_to_circle(im)
    im3.paste(im, (75, 75), mask=a1)
    im3.paste(im2, mask=a2)
    return im3
