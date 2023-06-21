from pathlib import Path
from nonebot import require, load_plugins
from nonebot.plugin import PluginMetadata


__version__ = "0.5.6"
__plugin_meta__ = PluginMetadata(
    name="求生之路小助手",
    description='群内对有关求生之路的查询和操作',
    usage="""
    查询：【关键词】([序号])
    """,
    type="application",
    homepage="https://github.com/Agnes4m/nonebot_plugin_l4d2_server",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": __version__,
        "author": "Agnes4m <Z735803792@163.com>",
    },
)

dir_ = Path(__file__).parent
require('nonebot_plugin_apscheduler')
load_plugins(str(dir_ / "nonebot_plugin_l4d2_server"))
