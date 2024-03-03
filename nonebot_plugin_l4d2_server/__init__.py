"""
* Copyright (c) 2023, Agnes Digital
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from nonebot import get_driver, require

require("nonebot_plugin_apscheduler")  # noqa: F401
require("nonebot_plugin_saa")  # noqa: F401
require("nonebot_plugin_htmlrender")  # noqa: F401
require("nonebot_plugin_txt2img")  # noqa: F401
scheduler = require("nonebot_plugin_apscheduler").scheduler

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

from .l4d2_data import sq_L4D2

# from .l4d2_file.input_json import *
from .l4d2_image.steam import url_to_byte_name
from .l4d2_push import scheduler  # noqa: F401
from .l4d2_utils.command import help_, search_api
from .l4d2_utils.config import l4_config
from .l4d2_utils.utils import upload_file
from .l4d2_web import web, webUI  # noqa: F401

driver = get_driver()

__version__ = "0.6.6"
__plugin_meta__ = PluginMetadata(
    name="求生之路小助手",
    description="可用于管理求生之路查服和本地管理",
    usage="群内对有关求生之路的查询和操作",
    type="application",
    homepage="https://github.com/Agnes4m/nonebot_plugin_l4d2_server",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": __version__,
        "author": "Agnes4m <Z735803792@163.com>",
    },
)


"""相当于启动就检查数据库"""


@help_.handle()
async def _(matcher: Matcher):
    msg = """=====求生机器人帮助=====
    1、电信服战绩查询【求生anne | Ranne[id/steamid/@]】
    2、电信服绑定【求生绑定[id/steamid]】",
    3、电信服状态查询【云xx】
    4、创意工坊下载【创意工坊下载[物品id/链接]】
    5、指定ip查询【求生ip[ip]】(可以是域名)
    6、求生喷漆制作【求生喷漆】
    7、本地服务器相关【l4地图上传】【l4地图改名】【l4地图删除】【l4路径】【l4插件】
    8、ip导入（私聊发送json文件，格式参考下方链接中readme）
    9、内置ip更新【l4公益服更新】【求生更新anne】
    项目地址:https://github.com/Agnes4m/nonebot_plugin_l4d2_server
    """
    await matcher.finish(msg)


@search_api.got("is_sure", prompt='如果需要上传，请发送 "yes"')
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent, state: T_State):
    if not l4_config.l4_group_upload:
        return
    is_sure = str(state["is_sure"])
    if is_sure == "yes":
        data_dict: dict = state["maps"][0]
        if isinstance(data_dict, dict):
            logger.info("开始上传")
            if l4_config.l4_only:
                reu = await url_to_byte_name(data_dict["url"], "htp")
            else:
                reu = await url_to_byte_name(data_dict["url"])
            if not reu:
                return
            data_file, file_name = reu
            if data_file:
                await matcher.send("获取地址成功，尝试上传")
                await upload_file(bot, event, data_file, file_name)
            else:
                await search_api.send("出错了，原因是下载链接不存在")
        else:
            ...
            # logger.info("开始上传")
            # for data_one in data_dict:
            #     reu = await url_to_byte_name(data_one["url"])
            #     if not reu:
            #         return
            #     data_file, file_name = reu
            #     await all_zip_to_one()
            #     await upload_file(bot, event, data_file, file_name)
    else:
        await matcher.finish("已取消上传")


# @reload_ip.handle()
# async def _(matcher:Matcher):
#     global matchers
#     await matcher.send('正在重载ip，可能需要一点时间')
#     for _, l4_matchers in matchers.items():
#         for l4_matcher in l4_matchers:
#             l4_matcher.destroy()
#     await get_des_ip()
#     await matcher.finish('已重载ip')


@driver.on_shutdown
async def close_db():
    """关闭数据库"""
    sq_L4D2._close()  # noqa: SLF001
