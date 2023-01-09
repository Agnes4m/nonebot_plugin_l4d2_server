from PIL import Image, ImageDraw, ImageFont
import asyncio
import asyncio
from pathlib import Path

from PIL import Image
from .download import get_head_by_user_id_and_save
from .send_image_tool import convert_img
from ..config import *




first_color = (242, 250, 242)
second_color = (57, 57, 57)


def font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(l4_font, size=size)


font_36 = font_origin(36)
font_40 = font_origin(40)
font_24 = font_origin(24)


async def draw_user_info_img(user_id, DETAIL_MAP:dict):
    based_w = 1080
    based_h = 1920
    #获取背景图
    img = Image.open(TEXT_PATH / 'back.png').resize((based_w, based_h)).convert("RGBA")
    #获取用户头像圆框
    user_status = Image.open(TEXT_PATH / 'head.png').resize((450,450)).convert("RGBA")
    temp = await get_head_by_user_id_and_save(user_id)
    user_head = await img_author(temp, user_status)
    r, g, b, a = user_status.split()
    #绘制头像框位置
    img.paste(user_head, (100, 100), mask=a) 
    # img_draw = ImageDraw.Draw(img)
    #h获取信息图片
    line = Image.open(TEXT_PATH / 'line3.png').resize((400, 60)).convert("RGBA")
    line_draw = ImageDraw.Draw(line)
    word = f"QQ:{user_id}"
    w, h = await linewh(line, word)
    line_draw.text((w, h), word, first_color, font_36, 'lm')
    #绘制QQ信息
    img.paste(line, (130,520), line)
    DETAIL_MAP:dict
    titles = []
    for title in DETAIL_MAP:
        titles.append(title)
    """
    DETAIL_MAP=｛
    结果:1
    玩家:爱丽数码
    分数:450
    国家:cn
    游玩时间:0.00 Seconds (0 min)
    最后上线:9.39 Hours ago
    }
    -----------------
    title[0]:Rank,
    title[1]:player,
    title[2]:points,
    title[3]:country,
    title[4]:playtime,
    title[5]:last_online,
    title[6]:steamid
    
    """
    
    DETAIL_right = {}
    DETAIL_right['结果'] = DETAIL_MAP['结果']
    DETAIL_right['玩家'] = DETAIL_MAP['玩家']
    DETAIL_right['分数'] = DETAIL_MAP['分数']
    DETAIL_right['steamid'] = DETAIL_MAP['steamid']
    DETAIL_more = {}
    DETAIL_more['游玩时间'] = DETAIL_MAP['游玩时间']
    DETAIL_more['最后上线'] = DETAIL_MAP['最后上线']
    
    tasks1 = []
    for key, value in DETAIL_right.items():
        tasks1.append(_draw_line(img, key, value, DETAIL_right))
    await asyncio.gather(*tasks1)
    
    baseinfo = Image.open(TEXT_PATH / 'line2.png').resize((900, 100)).convert("RGBA")
    baseword = '【基本信息】'
    w, h = await linewh(baseinfo, baseword)
    baseinfo_draw = ImageDraw.Draw(baseinfo)
    baseinfo_draw.text((w, h), baseword, first_color, font_40, 'lm')
    img.paste(baseinfo, (100, 600), baseinfo)
    
    tasks2 = []
    for key, value in DETAIL_more.items():
        tasks2.append(_draw_base_info_line(img, key, value, DETAIL_more))
    await asyncio.gather(*tasks2)
    
    res = await convert_img(img)
    return res
    

    

async def _draw_line(img: Image.Image, key, value, DETAIL_MAP):

    line = Image.open(TEXT_PATH / 'line3.png').resize((450, 68))
    line_draw = ImageDraw.Draw(line)
    word = f"{key}：{value}"
    w, h = await linewh(line, word)
    
    line_draw.text((70, h), word, first_color, font_36, 'lm')
    img.paste(line, (550, 100 + list(DETAIL_MAP.keys()).index(key) * 103), line)
    
async def _draw_base_info_line(img: Image.Image, key, value, DETAIL_MAP):

    line = Image.open(TEXT_PATH / 'line4.png').resize((900, 100))
    line_draw = ImageDraw.Draw(line)
    word = f"{key}：{value}"
    w, h = await linewh(line, word)
    
    line_draw.text((100, h), word, first_color, font_36, 'lm')
    img.paste(line, (100, 703 + list(DETAIL_MAP.keys()).index(key) * 103), line)
    
async def _draw_sect_info_line(img: Image.Image, key, value, DETAIL_MAP):

    line = Image.open(TEXT_PATH / 'line4.png').resize((900, 100))
    line_draw = ImageDraw.Draw(line)
    word = f"{key}：{value}"
    w, h = await linewh(line, word)
    
    line_draw.text((100, h), word, first_color, font_36, 'lm')
    img.paste(line, (100, 1565 + list(DETAIL_MAP.keys()).index(key) * 103), line)
        
    

async def img_author(img, bg):
    
    w, h = img.size
    alpha_layer = Image.new('L', (w, w), 0)
    draw = ImageDraw.Draw(alpha_layer)
    draw.ellipse((0, 0, w, w), fill=255)
    bg.paste(img, (88, 88), alpha_layer)
    
    return bg

async def linewh(line, word):
    lw, lh = line.size
    gs_font_36 = font_origin(36)
    w, h = gs_font_36.getsize(word)
    return (lw - w) / 2, lh / 2
    
