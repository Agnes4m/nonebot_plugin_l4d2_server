import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import aiofiles

# from ..utils.db_operation.db_operation import config_check

bot_start = Path().cwd() / "bot.py"
restart_sh_path = Path().cwd() / "gs_restart.sh"
update_log_path = Path(__file__).parent / "update_log.json"

_restart_sh = """#!/bin/bash
kill -9 {}
{} &"""


async def get_restart_sh(extra: str) -> str:
    args = f"{extra} {bot_start.absolute()!s}"
    return _restart_sh.format(str(bot_start.absolute()), args)


async def restart_genshinuid(send_type: str, send_id: str) -> None:
    # extra = ''
    # if await config_check('UsePoetry'):
    #     extra = 'poetry run '
    extra = sys.executable
    restart_sh = await get_restart_sh(extra)
    if not restart_sh_path.exists():
        async with aiofiles.open(restart_sh_path, "w", encoding="utf8") as f:
            await f.write(restart_sh)
        if platform.system() == "Linux":
            os.system(f"chmod +x {restart_sh_path!s}")  # noqa: ASYNC102
            os.system(f"chmod +x {bot_start!s}")  # noqa: ASYNC102
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    update_log = {
        "type": "restart",
        "msg": "重启完成!",
        "send_type": send_type,
        "send_to": send_id,
        "time": now_time,
    }
    async with aiofiles.open(str(update_log_path), mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(update_log))
    if platform.system() == "Linux":
        os.execl(str(restart_sh_path), " ")
    else:
        pid = os.getpid()
        subprocess.Popen(  # noqa: ASYNC101
            f"taskkill /F /PID {pid} & {extra} {bot_start}",
            shell=True,
        )


async def restart_message() -> dict:
    if update_log_path.exists():
        async with aiofiles.open(update_log_path, "r", encoding="utf-8") as f:
            content = await f.read()
            update_log = json.loads(content)
        msg = f'{update_log["msg"]}\n重启时间:{update_log["time"]}'
        update_log["msg"] = msg
        update_log_path.unlink()
        restart_sh_path.unlink()
        return update_log
    return {}
