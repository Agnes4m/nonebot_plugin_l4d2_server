"""Admin commands: image toggle, style switch, legacy reload, tj/zl/kl pickers."""

from __future__ import annotations

from pathlib import Path

from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_command, on_fullmatch
from nonebot_plugin_alconna import UniMessage

from config import config, config_manager
from registry import registry
from services import filter as svc_filter
from services import sourceban
from store import pages as pages_store

l4_toggle_image = on_command(
    "l4_toggle_image",
    aliases={"l4img", "l4图片"},
    permission=SUPERUSER,
)
l4_switch_style = on_command(
    "l4_switch_style",
    aliases={"l4style", "l4风格切换"},
    permission=SUPERUSER,
)
l4_reload_servers = on_command(
    "l4_reload",
    aliases={"l4reload", "l4刷新", "l4重载"},
)


@l4_toggle_image.handle()
async def _(args: Message = CommandArg()) -> None:
    arg = args.extract_plain_text().strip().lower()
    if arg == "开启":
        config_manager.update_image_config(enabled=True)
        await UniMessage.text("[l4]已开启图片模式").finish()
    elif arg == "关闭":
        config_manager.update_image_config(enabled=False)
        await UniMessage.text("[l4]已关闭图片模式").finish()
    await UniMessage.text("请在参数后加上开启或关闭").finish()


@l4_switch_style.handle()
async def _() -> None:
    if config.l4_style == "default":
        config_manager.update_style_config(style="old")
        await UniMessage.text("[l4]已切换为旧风格").finish()
    else:
        config_manager.update_style_config(style="default")
        await UniMessage.text("[l4]已切换为默认风格").finish()


@l4_reload_servers.handle()
async def _(args: Message = CommandArg()) -> None:
    if args.extract_plain_text().strip():
        return

    pages = await pages_store.load_pages()
    if pages:
        ok, fails = await sourceban.refresh_all_pages()
        from commands.query import refresh_server_command_rule
        refresh_server_command_rule()
        msg_lines = [f"重载完成：成功 {ok} 个组"]
        if fails:
            msg_lines.append("失败：\n" + "\n".join(fails))
        await UniMessage.text("\n".join(msg_lines)).send()
    else:
        await sourceban.reload_registry()
        from commands.query import refresh_server_command_rule
        refresh_server_command_rule()
        await UniMessage.text("重载ip完成").send()


# tj / zl / kl pickers, registered only when "云" group is known.
if "云" in registry.commands:
    ld_tj = on_fullmatch("tj")
    ld_zl = on_fullmatch("zl")
    ld_kl = on_fullmatch("kl")

    @ld_tj.handle()
    async def _(matcher) -> None:
        await matcher.send("正在寻找牢房信息")
        out = await svc_filter.pick_filtered(registry.get("云") or [], "tj")
        await matcher.finish(out)

    @ld_zl.handle()
    async def _(matcher) -> None:
        await matcher.send("正在寻找牢房信息")
        out = await svc_filter.pick_filtered(registry.get("云") or [], "zl")
        await matcher.finish(out)

    @ld_kl.handle()
    async def _(matcher) -> None:
        await matcher.send("正在寻找牢房信息")
        out = await svc_filter.pick_filtered(registry.get("云") or [], "kl")
        await matcher.finish(out)