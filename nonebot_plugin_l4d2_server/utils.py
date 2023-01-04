from nonebot.log import logger
import requests

def get_file(url,down_file):
    try:
        maps = requests.get(url)
        logger.info('已获取文件，尝试新建文件并写入')
        with open(down_file ,'wb') as mfile:
            logger.info('正在写入')
            mfile.write(maps.content)
            logger.info('下载成功')
            mes =('文件已下载,正在解压')
    except Exception as e:
        print(e)
        logger.info("文件获取不到/已损坏")
        mes = "寄"
    return mes