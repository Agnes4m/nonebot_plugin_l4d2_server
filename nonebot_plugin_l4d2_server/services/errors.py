"""统一业务异常类型。

handler 层约定::

    @matcher.handle()
    async def _():
        try:
            await do_something()
        except L4Error as e:
            await UniMessage.text(str(e)).finish()

按用途划分（每条都是 ``L4Error`` 子类，handler 一个 except 兜底即可）：

- ``L4ServerUnreachableError``：A2S 服务器持续不可达（多次重试仍超时）。
- ``L4TimeoutError``：A2S / HTTP 单次超时。
- ``L4InvalidInputError``：用户输入不合法（参数缺失、URL/ID 错误等）。
- ``L4NotFoundError``：资源未找到（组、服务器、收藏记录等）。
- ``L4HTTPError``：HTTP 请求失败（非 2xx 或网络异常），带 ``status``。

边界：

- A2S 单服 ``_a2s_one`` 仍然用空 ``SourceInfo``（max_players=0）作 sentinel——
  上层通过 ``server.max_players == 0`` 判断离线，不需要 ``L4Error``。
- ``a2s_info_batch`` 整体 gather 失败也吞掉、走空结果，避免一组服务器
  拖垮整批查询。
- HTTP 单次失败：``http_helpers._request`` 仍返回 ``{}``/HTML，由调用方
  决定是否升级为 ``L4HTTPError`` 重抛。

什么时候 ``raise``：

- 命令 handler 收到非法参数 → ``raise L4InvalidInputError(...)``
- 命令 handler 找不到目标资源 → ``raise L4NotFoundError(...)``
- 强制重试 / 手动 fetch 失败 → ``raise L4HTTPError(status=...)``

什么时候不要 ``raise``：

- 单服 A2S 失败：保持空 ``SourceInfo``（group 命令会把不在线服务器
  在图片底部以文字区块展示，给用户视觉提示比报错更有用）。
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
