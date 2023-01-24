from PIL import Image
import httpx
from bs4 import BeautifulSoup
import io
from ..config import l4_proxies

    
    
async def web_player(url) -> Image :
    """steam个人资料获取头像"""
    data = BeautifulSoup(await url_for_byte(url), 'html.parser')
    print(data)
    head = data.find("div", class_="playerAvatarAutoSizeInner")
    img_elements = head.find_all("img")
    if len(img_elements)== 1:
        for img_element in img_elements:
            head = await url_for_byte(img_element["src"])
        im = Image.open(io.BytesIO(head)).resize((225, 225)).convert("RGBA")
    if len(img_elements) == 2:
        head,headd = img_elements
        head = await url_for_byte(img_element["src"])
        head = await url_for_byte(img_element["src"])
    # 下面是边框，不一定有
    try:
        headd = data.select("html.responsive body.flat_page.profile_page.has_profile_background.GhostTheme.responsive_page div.responsive_page_frame.with_header div.responsive_page_content div#responsive_page_template_content.responsive_page_template_content div.no_header.profile_page.has_profile_background div.profile_header_bg div.profile_header_bg_texture div.profile_header div.profile_header_content div.playerAvatar.profile_header_size.in-game div.playerAvatarAutoSizeInner div.profile_avatar_frame img")
        im2 = Image.open(io.BytesIO(headd)).resize((185, 185)).convert("RGBA")
        r, g, b, a2 = im2.split()
        # im.paste(im2,(20,20),mask=a2)
    except IndexError:
        pass
    return im


async def url_to_byte(url):
    """所有url终将绳之以法"""
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    }
    data = httpx.get(url,headers=headers,timeout=60,verify=False).content
    return data

async def url_for_byte(url):
    """所有代理_url终将绳之以法"""
    if not l4_proxies:
        print("代理不存在")
        data = await url_to_byte(url)
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    }
    data = httpx.get(url,headers=headers,proxies=l4_proxies,timeout=60,verify=False).content
    return data