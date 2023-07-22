import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter


@pytest.mark.asyncio
async def test_init():
    nonebot.init()
    app = nonebot.get_asgi()

    driver = nonebot.get_driver()
    driver.register_adapter(ONEBOT_V11Adapter)

    nonebot.load_plugin("nonebot_plugin_l4d2_server")  # 加载重启插件

    # 测试代码
    assert True
