import httpx
from nonebot.log import logger
import asyncio
import hashlib
import os
from PIL import Image,ImageDraw
import io
from ..config import PLAYERSDATA,TEXT_PATH

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

    
def square_to_circle(im:Image):
    """im是正方形，变圆形"""
    size = im.size
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    # 将遮罩层应用到图像上
    im.putalpha(mask)
    return im

async def get_head_by_user_id_and_save(user_id):
    """qq转头像"""
    user_id = str(user_id)
    
    USER_HEAD_PATH = PLAYERSDATA / user_id / 'HEAD.png'
    DEFAULT_HEAD_PATH = TEXT_PATH / "template/player.jpg"
    ## im头像 im2头像框 im3合成
    if os.path.exists(USER_HEAD_PATH):
        logger.info("使用本地头像")
        im = Image.open(USER_HEAD_PATH).resize((280, 280)).convert("RGBA")
    else:
        if user_id == "1145149191810":
            logger.info("使用默认头像")
            im = Image.open(DEFAULT_HEAD_PATH).resize((300, 300)).convert("RGBA")
        else:
            try:
                logger.info("正在下载头像")
                image_bytes = await download_head(user_id)
                im = Image.open(io.BytesIO(image_bytes)).resize((280, 280)).convert("RGBA")
                if not os.path.exists(PLAYERSDATA / user_id):#用户文件夹不存在
                    os.makedirs(PLAYERSDATA / user_id)
                im.save(USER_HEAD_PATH, "PNG")
            except:
                logger.error("获取失败")
    im2 = Image.open(TEXT_PATH /"head.png").resize((450,450)).convert("RGBA")
    im3 = Image.new("RGBA", im2.size, (255,255,255,0))
    r, g, b, a1 = im.split()
    r, g, b, a2 = im2.split()
    im = square_to_circle(im)
    im3.paste(im,(75,75),mask=a1)
    im3.paste(im2,mask=a2)
    return im3

async def url_to_byte(url):
    """所有url终将绳之以法"""
    data = httpx.get(url).content
    return data
