import asyncio
import contextlib
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast

import a2s
import aiofiles
import ujson as json
from bs4 import BeautifulSoup, Tag
from httpx import AsyncClient
from nonebot.log import logger

from ...config import config
from ..utils import split_maohao
from .api import AnnePlayerApi, AnneSearchApi, WorkshopApi, anne_ban
from .models import (
    AnnePlayer2,
    AnnePlayerDetail,
    AnnePlayerError,
    AnnePlayerInf,
    AnnePlayerInfAvg,
    AnnePlayerInfo,
    AnnePlayerSur,
    AnneSearch,
    SourceBansInfo,
    WorksopInfo,
)

config_path = Path(config.l4_path) / "config.json"


class L4D2Api:
    ssl_verify = False
    _HEADER: Dict[str, str] = {  # noqa: RUF012
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko)"
        "Chrome/126.0.0.0"
        "Safari/537.36 Edg/126.0.0.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    }

    def safe_select(self, element: Optional[Tag], selector: str) -> List[Any]:
        """安全地调用 select 方法"""
        if isinstance(element, Tag):
            return element.select(selector)
        return []

    def safe_find_all(
        self,
        element: Optional[Tag],
        tag: str,
        class_: str = "",
    ) -> List[Any]:
        """安全地调用 find_all 方法"""
        if isinstance(element, Tag):
            return element.find_all(tag, class_=class_)
        return []

    async def a2s_server_info(
        self,
        ip: Tuple[str, int],
    ):
        try:
            server = await a2s.ainfo(
                ip,
                timeout=3,
                encoding="utf8",
            )

        except (
            asyncio.exceptions.TimeoutError,
            ConnectionRefusedError,
            socket.gaierror,
        ):
            server = a2s.SourceInfo(
                protocol=0,
                server_name="服务器无响应",
                map_name="无",
                folder="m",
                game="L4D2",
                app_id=114514,
                steam_id=0,
                player_count=0,
                max_players=0,
                bot_count=0,
                server_type="w",
                platform="w",
                password_protected=False,
                vac_enabled=False,
                version="1.0",
                edf=0,
                ping=0,
            )
            server.player_count = 0
            server.max_players = 0
            server.server_name = "服务器无响应"
            server.map_name = "无"
            server.folder = "m"
            server.vac_enabled = False
        return server

    async def a2s_info(
        self,
        ip_list: List[Tuple[str, int]],
        is_server: bool = True,
        is_player: bool = False,
    ) -> List[
        Tuple[Union[a2s.SourceInfo[str], a2s.GoldSrcInfo[str]], List[a2s.Player]]
    ]:
        msg_list: List[
            Tuple[Union[a2s.SourceInfo[str], a2s.GoldSrcInfo[str]], List[a2s.Player]]
        ] = []

        if ip_list:
            tasks = [
                asyncio.create_task(
                    self.process_message(ip, index, is_server, is_player),
                )
                for index, ip in enumerate(ip_list)
            ]

            try:
                results = await asyncio.gather(*tasks)
                msg_list = [r for r in results if r is not None]
            except Exception as e:
                logger.error(f"获取服务器信息时发生错误: {e}")

        # 使用稳定的排序方式，避免服务器频繁变动位置
        return sorted(
            msg_list,
            key=lambda x: (
                getattr(x[0], "steam_id", float("inf")) is None,
                getattr(x[0], "steam_id", float("inf")),
            ),
        )

    async def process_message(
        self,
        ip: Tuple[str, int],
        index: int,
        is_server: bool,
        is_player: bool,
    ):
        play: List[a2s.Player] = []
        server: Union[a2s.SourceInfo, a2s.GoldSrcInfo]
        if is_server:
            try:
                server = await a2s.ainfo(
                    ip,
                    timeout=3,
                    encoding="utf8",
                )

                if server is not None:
                    server.steam_id = index  # type: ignore

            except (
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                socket.gaierror,
            ):
                server = a2s.SourceInfo(
                    protocol=0,
                    server_name="服务器无响应",
                    map_name="无",
                    folder="m",
                    game="L4D2",
                    app_id=114514,
                    steam_id=index,
                    player_count=0,
                    max_players=0,
                    bot_count=0,
                    server_type="w",
                    platform="w",
                    password_protected=False,
                    vac_enabled=False,
                    version="1.0",
                    edf=0,
                    ping=0,
                )
                server.steam_id = index
                server.player_count = 0
                server.max_players = 0
                server.server_name = "服务器无响应"
                server.map_name = "无"
                server.folder = "m"
                server.vac_enabled = False
                is_player = False

        if is_player:
            with contextlib.suppress(
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                socket.gaierror,
            ):
                play = await a2s.aplayers(ip, timeout=3, encoding="utf8")
        else:
            play = []
        return server, play

    async def _server_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        header: Dict[str, str] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any] | list] = None,
        data: Optional[Dict[str, Any]] = None,
        is_json: bool = True,
    ) -> Union[Dict[str, Any], BeautifulSoup]:  # type: ignore
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
                    raw_data = resp.json()
                except:  # noqa: E722
                    _raw_data = resp.text
                    try:
                        raw_data = json.loads(_raw_data)
                    except:  # noqa: E722
                        raw_data = {
                            "result": {"error_code": -999, "data": _raw_data},
                        }
                try:
                    if not raw_data["result"]:
                        return raw_data
                except Exception:
                    return raw_data
                logger.debug(f"Raw data: {raw_data}")
                if (
                    "result" in raw_data
                    and "error_code" in raw_data["result"]
                    and raw_data.get("code") != 200
                ):
                    return raw_data["result"]["error_code"]
                return raw_data
            html_content = resp.content
            return BeautifulSoup(html_content, "lxml")

    async def get_sourceban(self, tag: str = "云", url: str = anne_ban):
        """
        异步函数，从sourceban++获取服务器列表，目前未做名称处理。

        Args:
            tag (str): 用于标识不同来源的标签，默认为"云"。
            url (str): SourceBan的URL，默认为anne_ban。

        Returns:
            list: 包含服务器信息的列表。

        """
        if not (url.startswith(("http://", "https://"))):
            url = "http://" + url  # 默认添加 http://
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
        tr_tags = self.safe_select(tbody, "tr")
        for index, tr in enumerate(tr_tags):
            td_tags = self.safe_select(tr, "td")
            for num, td in enumerate(td_tags):
                if num == 4:
                    host, port = split_maohao(td.text)
                    server_list.append(
                        SourceBansInfo(index=index, host=host, port=port),
                    )

        if not Path(Path(config.l4_path) / "config.json").is_file():
            async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
                await f.write("{}")
        with (Path(config.l4_path) / "config.json").open("r", encoding="utf-8") as f:
            content = f.read().strip()
            ip_json = json.loads(content)
        if tag in ip_json:
            url = ip_json[tag]
        tag_path = Path(Path(config.l4_path) / f"l4d2/{tag}.json")

        async with aiofiles.open(tag_path, "w", encoding="utf-8") as f:
            up_data = {}
            for server in server_list:
                new_dict = {}
                new_dict["id"] = int(server.index) + 1
                new_dict["ip"] = server.host + ":" + str(server.port)
                up_data.update(new_dict)
            json.dump(up_data, f, ensure_ascii=False, indent=4)
        return server_list

    async def get_anne_steamid(self, name: str):
        """从电信anne服搜索昵称获取steamid"""
        soup = await self._server_request(
            url=AnneSearchApi,
            data={"search": name},
            method="POST",
            is_json=False,
        )
        if not isinstance(soup, BeautifulSoup):
            return None
        server_list = []
        tbody = soup.select_one("tbody")
        if tbody is None:
            return None
        tr_tags = tbody.select("tr")
        for tr in tr_tags:
            onclick = tr.get("onclick")
            if onclick is None or isinstance(onclick, list):
                continue
            steamid = onclick.split("steamid=")[1].replace("'", "")
            td_tags = tr.select("td")
            server_list.append(
                {
                    "steamid": steamid,
                    "rank": td_tags[0].text.strip(),
                    "name": td_tags[1].text.strip(),
                    "score": td_tags[2].text.strip(),
                    "play_time": td_tags[3].text.strip(),
                    "last_time": td_tags,
                },
            )
        logger.debug(server_list)
        return cast(List[AnneSearch], server_list)

    async def get_anne_playerdetail(self, steamid: str):
        """从电信anne服通过steamid获取战绩"""
        soup = await self._server_request(
            url=AnnePlayerApi,
            method="GET",
            params={"steamid": steamid},
            is_json=False,
        )
        if not isinstance(soup, BeautifulSoup):
            return None

        tbody = cast(BeautifulSoup, soup).find(
            "div",
            class_="content text-center text-md-left",
            style="background-color: #f2f2f2;",
        )
        if tbody is None:
            return None

        def get_table_dict(table, keys):
            trs = table.select("tr")
            return {
                key: trs[i].select("td")[1].text.strip() for i, key in enumerate(keys)
            }

        kill_tag = cast(Tag, tbody).find(
            "div",
            class_="card-body worldmap d-flex flex-column justify-content-center text-center",
        )

        tbody_tags = []
        if isinstance(tbody, Tag):
            tbody_tags = tbody.find_all(
                "table",
                class_="table content-table-noborder text-left",
            )
        if len(tbody_tags) < 6:
            return None

        info_keys = ["name", "avatar", "steamid", "playtime", "lasttime"]
        detail_keys = [
            "rank",
            "source",
            "avg_source",
            "kills",
            "kills_people",
            "headshots",
            "avg_headshots",
            "map_play",
        ]
        error_keys = [
            "mistake_shout",
            "kill_friend",
            "down_friend",
            "abandon_friend",
            "put_into",
            "agitate_witch",
        ]
        inf_avg_keys = [
            "avg_smoker",
            "avg_boomer",
            "avg_hunter",
            "avg_charger",
            "avg_spitter",
            "avg_jockey",
            "avg_tank",
        ]
        sur_keys = [
            "map_clear",
            "prefect_into",
            "get_oil",
            "ammo_arrange",
            "adrenaline_give",
            "pills_give",
            "first_aid_give",
            "friend_up",
            "diss_friend",
            "save_friend",
            "protect_friend",
            "pro_from_smoker",
            "pro_from_hunter",
            "pro_from_charger",
            "pro_from_jockey",
            "melee_charge",
            "tank_kill",
            "witch_instantly_kill",
        ]
        inf_keys = [
            "sur_ace",
            "sur_down",
            "boommer_hit",
            "hunter_prefect",
            "hunter_success",
            "tank_damage",
            "charger_multiple",
        ]

        info_dict = get_table_dict(tbody_tags[0], info_keys)
        detail_dict = get_table_dict(tbody_tags[1], detail_keys)
        error_dict = get_table_dict(tbody_tags[2], error_keys)
        inf_avg_dict = get_table_dict(tbody_tags[3], inf_avg_keys)
        sur_dict = get_table_dict(tbody_tags[4], sur_keys)
        inf_dict = get_table_dict(tbody_tags[5], inf_keys)

        info_dict = cast(AnnePlayerInfo, info_dict)
        detail_dict = cast(AnnePlayerDetail, detail_dict)
        error_dict = cast(AnnePlayerError, error_dict)
        inf_avg_dict = cast(AnnePlayerInfAvg, inf_avg_dict)
        sur_dict = cast(AnnePlayerSur, sur_dict)
        inf_dict = cast(AnnePlayerInf, inf_dict)

        out_dict = {
            "kill_msg": kill_tag.text.strip() if kill_tag else "",
            "info": info_dict,
            "detail": detail_dict,
            "inf_avg": inf_avg_dict,
            "sur": sur_dict,
            "inf": inf_dict,
            "error": error_dict,
        }

        return cast(AnnePlayer2, out_dict)

    async def workshops(self, workshop_id: str) -> WorksopInfo:
        workshop_json = await self._server_request(
            url=WorkshopApi,
            json=[int(workshop_id)],
            header=self._HEADER,
            method="POST",
            is_json=True,
        )
        return cast(WorksopInfo, workshop_json[0])


L4API = L4D2Api()
