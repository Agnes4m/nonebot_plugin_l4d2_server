
from PIL import Image
from srctools.vtf import VTF, ImageFormats
from nonebot.log import logger
from io import BytesIO

async def img_to_vtf(pic_byte:bytes,tag):
    pic = BytesIO(pic_byte)
    pic = Image.open(pic).convert('RGBA')
    vtf_io = BytesIO()
    vtf_ = VTF(1024, 1024, fmt = ImageFormats.DXT5,thumb_fmt = ImageFormats.DXT1,version=(7,2))
    if tag == '覆盖':
        logger.info(tag)
        img2 = Image.new('RGBA',(1024, 1024), (255, 255, 255,0))
        r, g, b, a = pic.split()
        img2.paste(pic,mask=a)
        pic = pic.resize((1024,1024))
    elif tag == '填充':
        logger.info(tag)
        w, h = pic.size
        a = w if w >=h else h
        point = a/1024
        pic.resize((w*point,h*point))
    else:
        logger.info('拉伸')
        pic = pic.resize((1024,1024))
    largest_frame = vtf_.get() 
    largest_frame.copy_from(pic.tobytes(), ImageFormats.RGBA8888)
    vtf_.save(file = vtf_io)
    return vtf_io
