
from pathlib import Path

from nonebot import on_command
from nonebot.log import logger
from nonebot_plugin_alconna import UniMessage

from ..config import config
from ..l4_image.convert import text2pic

local_path_list = config.l4_local
if not local_path_list:
    logger.warning("未填写本地服务器路径,如果想要使用本地服务器功能,请填写本地服务器路径")
else:
    local_path: list[Path] = []
    for folder_path in local_path_list:
        path = Path(folder_path)  
        
        if path.is_dir():  
            for nextdir in path.iterdir():  
                # 如果找到了名为left4dead2的目录，返回True  
                if nextdir.name == "left4dead2" and nextdir.is_dir():  
                    local_path.append(nextdir)
            continue
    logger.info(f"本地服务器路径列表:{local_path}")
    
    global map_index
    map_index = 0

    search_map = on_command("l4map", aliases={"l4地图查询", "l4地图"}, priority=5, block=True)
    @search_map.handle()
    async def _():
        supath = local_path[map_index] / "addons"
        vpk_list: list[str] = []
        print(supath)
        if supath.is_dir():
            for sudir in supath.iterdir():
                logger.info(f"找到文件:{sudir}")
                if sudir.is_file() and sudir.name.endswith(".vpk"):
                    vpk_list.append(sudir.name)
        if not vpk_list:
            await UniMessage.text("未找到可用的VPK文件").finish()
        out_msg = "\n".join(f"{index + 1}、{line}" for index, line in enumerate(vpk_list)) 
        
        img = await text2pic(f"服务器地图:\n{out_msg}")
        await UniMessage.image(raw=img).send()