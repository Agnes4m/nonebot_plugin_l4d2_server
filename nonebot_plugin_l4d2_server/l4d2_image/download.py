import httpx
from nonebot.log import logger
import asyncio
import hashlib
import os
from PIL import Image
import io
from ..config import PLAYERSDATA

async def download_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url, timeout=20)
                resp.raise_for_status()
                return resp.content
            except Exception as e:
                logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                await asyncio.sleep(3)
    raise Exception(f"{url} 下载失败！")

async def download_head(user_id: str) -> bytes:
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
    data = await download_url(url)
    if hashlib.md5(data).hexdigest() == "acef72340ac0e914090bd35799f5594e":
        url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=100"
        data = await download_url(url)
    return data

async def get_head_by_user_id_and_save(user_id):
    """qq转头像"""
    user_id = str(user_id)

    USER_HEAD_PATH = PLAYERSDATA / user_id / 'HEAD.png'
    
    if os.path.exists(USER_HEAD_PATH):
        logger.info("头像已存在")
        im = Image.open(USER_HEAD_PATH).resize((280, 280)).convert("RGBA")
        return im
    else:
        try:
            logger.info("头像不存在，开始下载")
            image_bytes = await download_head(user_id)
            im = Image.open(io.BytesIO(image_bytes)).resize((280, 280)).convert("RGBA")
            if not os.path.exists(PLAYERSDATA / user_id):#用户文件夹不存在
                os.makedirs(PLAYERSDATA / user_id)
            im.save(USER_HEAD_PATH, "PNG")
        except:
            logger.error("获取头像出错")
    
        return im