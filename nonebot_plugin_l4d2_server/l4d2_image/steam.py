# from PIL import Image
# from bs4 import BeautifulSoup
from urllib.parse import unquote

import aiohttp
import httpx

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"  # noqa: E501
}


async def url_to_byte(url: str, filename: str = ""):
    """获取URL数据的字节流"""

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=600) as response:
            if response.status == 200:
                return await response.read()
            else:
                return None


async def url_to_byte_name(url: str, filename: str = ""):
    """获取URL数据的字节流"""

    if filename == "htp":
        response = httpx.get(url, headers=headers, timeout=600)
        content_disposition = response.headers.get("Content-Disposition")
        if not content_disposition:
            return None
        elif "''" in content_disposition:
            file_name = content_disposition.split("''")[-1]
        else:
            file_name = content_disposition
        file_name = unquote(file_name)
        if response.content and file_name:
            return [response.content, file_name]
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=600) as response:
                content_disposition = response.headers.get("Content-Disposition")
                if not content_disposition:
                    return
                if "''" in content_disposition:
                    file_name = content_disposition.split("''")[-1]
                else:
                    file_name = content_disposition
                if not file_name:
                    file_name = "anyone"
                file_name = unquote(file_name)
                if response.status == 200:
                    return [await response.read(), file_name]
                else:
                    return None
