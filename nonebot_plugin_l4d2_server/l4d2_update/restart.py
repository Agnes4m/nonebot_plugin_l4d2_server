import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# from ..utils.db_operation.db_operation import config_check

bot_start = Path().cwd() / "bot.py"
restart_sh_path = Path().cwd() / "gs_restart.sh"
update_log_path = Path(__file__).parent / "update_log.json"

_restart_sh = """#!/bin/bash
kill -9 {}
{} &"""


async def get_restart_sh(extra: str) -> str:
    args = f"{extra} {str(bot_start.absolute())}"
    return _restart_sh.format(str(bot_start.absolute()), args)


async def restart_genshinuid(send_type: str, send_id: str) -> None:
    # extra = ''
    # if await config_check('UsePoetry'):
    #     extra = 'poetry run '
    extra = sys.executable
    restart_sh = await get_restart_sh(extra)
    if not restart_sh_path.exists():
        with open(restart_sh_path, "w", encoding="utf8") as f:
            f.write(restart_sh)
        if platform.system() == "Linux":
            os.system(f"chmod +x {str(restart_sh_path)}")
            os.system(f"chmod +x {str(bot_start)}")
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    update_log = {
        "type": "restart",
        "msg": "重启完成!",
        "send_type": send_type,
        "send_to": send_id,
        "time": now_time,
    }
    with open(str(update_log_path), "w", encoding="utf-8") as f:
        json.dump(update_log, f)
    if platform.system() == "Linux":
        os.execl(str(restart_sh_path), " ")
    else:
        pid = os.getpid()
        subprocess.Popen(
            f"taskkill /F /PID {pid} & {extra} {bot_start}",
            shell=True,
        )


async def restart_message() -> dict:
    if update_log_path.exists():
        with open(update_log_path, "r", encoding="utf-8") as f:
            update_log = json.load(f)
        msg = f'{update_log["msg"]}\n重启时间:{update_log["time"]}'
        update_log["msg"] = msg
        os.remove(update_log_path)
        os.remove(restart_sh_path)
        return update_log
    else:
        return {}
