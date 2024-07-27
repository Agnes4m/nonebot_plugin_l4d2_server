import asyncio
import contextlib
import re
import socket
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast

import a2s
import ujson as js
from httpx import AsyncClient
from lxml import etree
from bs4 import BeautifulSoup

from ..utils import split_maohao
from .api import AnneSearchApi, anne_ban, anne_rank
from .models import AnneSearch, SourceBansInfo


class L4D2Api:
    ssl_verify = False
    _HEADER: Dict[str, str] = {  # noqa: RUF012
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko)"
        "Chrome/126.0.0.0"
        "Safari/537.36 Edg/126.0.0.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async def a2s_info(
        self,
        ip_list: List[Tuple[str, int]],
        is_server: bool = True,
        is_player: bool = False,
    ) -> List[Tuple[a2s.SourceInfo, List[a2s.Player]]]:
        msg_list: List[Tuple[a2s.SourceInfo, List[a2s.Player]]] = []

        tasks = []  # 用来保存异步任务
        if ip_list != []:
            for index, i in enumerate(ip_list):
                try:
                    tasks.append(
                        asyncio.create_task(
                            self.process_message(
                                i,
                                index,
                                is_server,
                                is_player,
                            ),
                        ),
                    )
                except ValueError:
                    continue  # 处理异常情况

            msg_list = await asyncio.gather(*tasks)
            sorted_msg_list = sorted(msg_list, key=lambda x: x[0].steam_id)

        return sorted_msg_list

    async def process_message(
        self,
        ip: Tuple[str, int],
        index: int,
        is_server: bool,
        is_player: bool,
    ):
        server: a2s.SourceInfo = a2s.SourceInfo()
        play: List[a2s.Player] = []
        if is_server:
            try:
                server = await a2s.ainfo(ip)
                if server is not None:
                    server.steam_id = index

            except (
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                socket.gaierror,
            ):
                server.steam_id = index
                server.player_count = 0
                server.max_players = 0
                server.server_name = "服务器无响应"
                server.map_name = "无"
                server.folder = "m"
                server.vac_enabled = False

        if is_player:
            with contextlib.suppress(
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                socket.gaierror,
            ):
                play = await a2s.aplayers(ip)
        return server, play

    async def _server_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        header: Dict[str, str] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_json: bool = True,
    ):
        header = deepcopy(self._HEADER)

        if json is not None:
            method = "POST"

        async with AsyncClient(verify=self.ssl_verify) as client:
            resp = await client.request(
                method,
                url=url,
                headers=header,
                params=params,
                json=json,
                data=data,
                timeout=300,
            )

            if is_json:
                try:
                    raw_data = await resp.json()
                except:  # noqa: E722
                    _raw_data = resp.text
                    try:
                        raw_data = js.loads(_raw_data)
                    except:  # noqa: E722
                        raw_data = {
                            "result": {"error_code": -999, "data": _raw_data},
                        }
                try:
                    if not raw_data["result"]:
                        return raw_data
                except Exception:
                    return raw_data
                if (
                    "result" in raw_data
                    and "error_code" in raw_data["result"]
                    and raw_data["code"] != 0
                ):
                    return raw_data["result"]["error_code"]
                return raw_data
            html_content = resp.text
            return BeautifulSoup(html_content, "lxml")

    async def get_sourceban(self, url: str = anne_ban):
        """从sourceban++获取服务器列表，目前未做名称处理"""
        soup = await self._server_request(
            url=url,
            is_json=False,
        )
        if not isinstance(soup, BeautifulSoup):
            return []
        server_list = []

        tbody = soup.select_one("tbody")
        if tbody is None:
            return []
        tr_tags = tbody.select("tr")
        for index, tr in enumerate(tr_tags):
            td_tags = tr.select("td")
            # print(td_set)
            for num, td in enumerate(td_tags):
                if num == 4:
                    host, port = split_maohao(td.text)
                    server_list.append(
                        SourceBansInfo(index=index, host=host, port=port)
                    )

        return server_list

    async def get_anne_player(self):
        tree = await self._server_request(
            url=anne_rank,
            is_json=False,
        )  # type: ignore

        theme_msg = tree.xpath("/html/body/div[6]/div/div[4]/div/h5/text()")
        return [str(tr) for tr in theme_msg]

    async def get_anne_steamid(self, name: str):
        """从电信anne服搜索昵称获取steamid"""
        tree = await self._server_request(
            url=AnneSearchApi,
            json={"search": name},
            method="POST",
            is_json=False,
        )
        # msg = etree.tostringlist(tree)

        target_element = tree.xpath(
            "/html/body/div[6]/div/div[3]/div/table",
        )
        print(etree.tostringlist(target_element[0]))
        server_list = []
        # for tr in target_element:
        for tr in target_element:
            steamid = tr.get("onclick").split("steamid=")[1].replace("'", "")
            rank = tr.xpath("./td[0]/text()")[0].strip()
            name = tr.xpath("./td[1]/text()")[0].strip()
            score = tr.xpath("./td[2]/text()")[0].strip()
            play_time = tr.xpath("./td[3]/text()")[0].strip()
            last_time = tr.xpath("./td[4]/text()")[0].strip()
            server_list.append(
                {
                    "steamid": steamid,
                    "rank": rank,
                    "name": name,
                    "score": score,
                    "play_time": play_time,
                    "last_time": last_time,
                },
            )
        print(server_list)
        return cast(List[AnneSearch], server_list)


L4API = L4D2Api()
