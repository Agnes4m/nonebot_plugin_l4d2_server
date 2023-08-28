import json
from pathlib import Path
from typing import Dict, List

from nonebot import on_notice
from nonebot.adapters.onebot.v11 import NoticeEvent
from nonebot.log import logger
from nonebot.matcher import Matcher

from ..l4d2_image.steam import url_to_msg

upload = on_notice(priority=1)


@upload.handle()
async def _(matcher: Matcher, event: NoticeEvent):
    try:
        arg = event.dict()
        files: dict = arg["file"]
        name: str = files["name"]
        if arg["notice_type"] == "offline_file" and name.endswith(".json"):
            try:
                msg = await url_to_msg(files["url"])
                if not msg:
                    return
                jsons: Dict[str, List[Dict[str, str]]] = json.loads(msg)
            except json.decoder:
                logger.info("求生json格式不正确")
                await matcher.finish("求生json格式不正确")
                return
            if not validate_json(jsons):
                logger.info("求生json格式不正确")
                await matcher.finish("求生json格式不正确")
            print(name)
            key = await up_date(jsons, name)
            if key:
                # logger.info(jsons)
                msg = "输入成功\n"
                for key, value in jsons.items():
                    msg += f"【{key}】指令：{len(value)}个\n"
                    logger.info(msg)
                await matcher.send(msg)
    except KeyError:
        pass


async def validate_json(json_data):
    try:
        data = json.loads(json_data)
        if not isinstance(data, dict):
            return False

        for key, value in data.items():
            if not isinstance(value, list):
                return False
            for item in value:
                if not isinstance(item, dict):
                    return False
                if not all(key in item for key in ["id", "ip"]):
                    return False
        if True:
            return True

    except json.JSONDecodeError:
        return False


async def up_date(data: Dict[str, List[Dict[str, str]]], name: str):
    print(data)
    directory = Path("data/L4D2/l4d2")
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / name
    with file_path.open("w") as json_file:
        json.dump(data, json_file)

    return True
