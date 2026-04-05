import pytest
from pytest_asyncio import is_async_test


def pytest_configure(config: pytest.Config) -> None:
    from nonebug import NONEBOT_INIT_KWARGS

    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi+~websockets+~httpx",
        "log_level": "DEBUG",
    }


def pytest_collection_modifyitems(items: list[pytest.Item]):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
def load_adapters(nonebug_init: None):  # noqa: ARG001, PT004
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Adapter as AdapterV11

    driver = get_driver()
    driver.register_adapter(AdapterV11)
