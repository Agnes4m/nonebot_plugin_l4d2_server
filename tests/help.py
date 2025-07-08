from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import Message, MessageEvent, Sender
from nonebot.log import logger


@pytest.mark.asyncio
async def test_init():
    nonebot.init(_env_file=Path(__file__).parent / "test")

    driver = nonebot.get_driver()
    driver.register_adapter(ONEBOT_V11Adapter)
    from ..nonebot_plugin_l4d2_server import __main__ as __main__

    nonebot.load_plugin(
        Path(__file__).parent / "nonebot_plugin_l4d2_server",
    )

    await test_help_command()

    assert True


async def test_help_command():
    from ..nonebot_plugin_l4d2_server import __main__ as __main__

    # 模拟一个消息事件
    bot = Bot(adapter=ONEBOT_V11Adapter, self_id=20001)

    event = MessageEvent(
        time=int(datetime.now().timestamp()),  # 必需字段
        post_type="message",  # 必需字段
        message_type="private",
        message_id=12345,
        user_id=10001,
        message=Message("l4帮助"),
        self_id="20001",
        sub_type="friend",
        raw_message="l4帮助",  # 必需字段
        font=0,
        sender=Sender(user_id=114515, nickname="测试用户"),  # 必需字段
    )

    with patch.object(logger, "info") as mock_logger_info:
        await bot.handle_event(event)
        mock_logger_info.assert_called_once_with("开始执行测试")
