"""统一业务异常类型。

handler 层用 ``except L4Error as e: await UniMessage.text(str(e)).finish()``
收敛错误处理；具体异常按用途划分，便于上层精细处理或日志分级。

注意：A2S / HTTP 底层仍以"返回 sentinel / None"为主，本模块只覆盖
那些上层希望显式抛错的场景（参数校验、资源不存在、HTTP 失败重试抛错等）。
"""

from __future__ import annotations


class L4Error(Exception):
    """所有插件业务异常的基类。"""


class L4ServerUnreachableError(L4Error):
    """A2S 服务器持续不可达。"""


class L4TimeoutError(L4Error):
    """A2S / HTTP 请求超时。"""


class L4InvalidInputError(L4Error):
    """用户输入不合法（参数缺失、URL/ID 错误等）。"""


class L4NotFoundError(L4Error):
    """资源未找到（组、服务器、收藏记录等）。"""


class L4HTTPError(L4Error):
    """HTTP 请求失败（非 2xx 或网络异常），可能可重试。"""

    def __init__(self, msg: str, *, status: int | None = None) -> None:
        super().__init__(msg)
        self.status = status
