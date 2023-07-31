import asyncio
from pathlib import Path

import aiofiles
from rcon.source import rcon

from ..l4d2_utils.config import CHECK_FILE, l4_config


async def rcon_server(password: str, msg: str):
    # response = await rcon(command=msg, host=l4_host, port=l4_port, passwd=password,encoding='utf-8')
    # return response
    try:
        return await asyncio.wait_for(
            rcon(
                command=msg,
                host=l4_config.l4_ipall[CHECK_FILE]["host"],
                port=l4_config.l4_ipall[CHECK_FILE]["port"],
                passwd=password,
            ),
            timeout=30,
        )
    except asyncio.TimeoutError:
        return "超时"


async def read_server_cfg_rcon():
    """如果没有输入rcon，尝试自动获取"""
    if not l4_config.l4_ipall[CHECK_FILE]["rcon"]:
        cfg_server = Path(
            l4_config.l4_ipall[CHECK_FILE]["location"],
            "left4dead2/cfg/server.cfg",
        )
        async with aiofiles.open(cfg_server, "r") as cfg:
            content: str = await cfg.read()
            lines = content.split("\n")
            for line in lines:
                if line.startswith("rcon_password"):
                    password = line.split(" ")[-1]
                    return password.strip('"')
    return l4_config.l4_ipall[CHECK_FILE]["rcon"]
