from pathlib import Path

import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter


@pytest.mark.asyncio
async def test_init():
    nonebot.init()

    driver = nonebot.get_driver()
    driver.register_adapter(ONEBOT_V11Adapter)
    from .nonebot_plugin_l4d2_server import __main__ as __main__

    nonebot.load_plugin(
        Path(__file__).parent / "nonebot_plugin_l4d2_server",
    )

    # 测试代码
    assert True
