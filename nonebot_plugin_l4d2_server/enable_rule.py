"""全局开关：``L4_ENABLE=false`` 时插件所有指令都不再匹配。

为什么不用 ``run_preprocessor`` 抛 ``SkippedException``：NoneBot 2.5 的
``_apply_run_preprocessors`` 用 ``run_coro_with_catch(proc(...), (SkippedException,))``
把该异常就地吞掉，取消不了 matcher。规则（``Rule``）在匹配阶段求值，返回
``False`` 就等于"这条指令不存在"，正是总开关需要的语义。
"""

from __future__ import annotations

from nonebot.rule import Rule

from .config import config


async def _l4_enabled() -> bool:
    return bool(config.l4_enable)


#: 叠在任意 rule 前面的全局开关。
L4_ENABLED = Rule(_l4_enabled)


def with_enable_guard(rule: Rule | None) -> Rule:
    """给已有 rule 叠上全局开关；``rule`` 为空时只返回开关本身。"""
    return L4_ENABLED & rule if rule is not None else L4_ENABLED


def apply_enable_guard_to_existing() -> int:
    """把全局开关叠到此刻已注册的所有本插件 matcher 上，返回处理数量。

    在 ``commands/__init__.py`` 导入完全部指令模块后调用一次即可；对已经叠过
    的 matcher 重复调用是安全的（``Rule`` 组合幂等，只是多一层求值）。
    """
    from nonebot.matcher import matchers

    count = 0
    for handlers in matchers.values():
        for handler in handlers:
            if getattr(handler, "plugin_id", None) != "nonebot_plugin_l4d2_server":
                continue
            handler.rule = with_enable_guard(getattr(handler, "rule", None))
            count += 1
    return count
