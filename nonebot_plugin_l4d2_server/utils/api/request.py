import asyncio
import contextlib
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, cast

import a2s
import aiofiles
import ujson as js
import ujson as json
from bs4 import BeautifulSoup
from httpx import AsyncClient

from ...config import config

# from nonebot.log import logger
from ..utils import split_maohao
from .api import AnnePlayerApi, AnneSearchApi, anne_ban
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
    }

    async def a2s_info(
        self,
        ip_list: List[Tuple[str, int]],
        is_server: bool = True,
        is_player: bool = False,
    ) -> List[Tuple[a2s.SourceInfo, List[a2s.Player]]]:
        msg_list: List[Tuple[a2s.SourceInfo, List[a2s.Player]]] = []
        sorted_msg_list = []
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
        play: List[a2s.Player] = []
        if is_server:
            try:
                server: a2s.SourceInfo = await a2s.ainfo(ip, timeout=3, encoding="utf8")

                if server is not None:
                    server.steam_id = index

            except (
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                socket.gaierror,
            ):
                server: a2s.SourceInfo = a2s.SourceInfo(
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

        if is_player:
            with contextlib.suppress(
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                socket.gaierror,
            ):
                play = await a2s.aplayers(ip, timeout=3, encoding="utf8")
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
            html_content = resp.content
            return BeautifulSoup(html_content, "lxml")

    async def get_sourceban(self, tag: str = "云", url: str = anne_ban):
        """从sourceban++获取服务器列表，目前未做名称处理"""
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
        tr_tags = tbody.select("tr")
        for index, tr in enumerate(tr_tags):
            td_tags = tr.select("td")
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
            print(Path(Path(config.l4_path) / f"l4d2/{tag}.json"))
            up_data = {}
            for server in server_list:
                new_dict = {}
                new_dict["id"] = int(server.index) + 1
                new_dict["ip"] = server.host + ":" + str(server.port)
                up_data.update(new_dict)
            print(up_data)
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
        print(server_list)
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

        tbody = soup.find(
            "div",
            class_="content text-center text-md-left",
            style="background-color: #f2f2f2;",
        )
        if tbody is None:
            return None
        kill_tag = tbody.find(
            "div",
            class_="card-body worldmap d-flex flex-column justify-content-center text-center",
        )

        tbody_tags = tbody.find_all(
            "table",
            class_="table content-table-noborder text-left",
        )
        print(len(tbody_tags))
        info_tag = tbody_tags[0]
        detail_tag = tbody_tags[1]
        error_tag = tbody_tags[2]
        inf_avg_tag = tbody_tags[3]
        sur_tag = tbody_tags[4]
        inf_tag = tbody_tags[5]

        info_tr = info_tag.select("tr")
        info_dict = {
            "name": info_tr[0].select("td")[1].text.strip(),
            "avatar": info_tr[1].select("td")[1].text.strip(),
            "steamid": info_tr[2].select("td")[1].text.strip(),
            "playtime": info_tr[3].select("td")[1].text.strip(),
            "lasttime": info_tr[4].select("td")[1].text.strip(),
        }
        detail_tag = {
            "rank": detail_tag.select("tr")[0].select("td")[1].text.strip(),
            "source": detail_tag.select("tr")[1].select("td")[1].text.strip(),
            "avg_source": detail_tag.select("tr")[2].select("td")[1].text.strip(),
            "kills": detail_tag.select("tr")[3].select("td")[1].text.strip(),
            "kills_people": detail_tag.select("tr")[4].select("td")[1].text.strip(),
            "headshots": detail_tag.select("tr")[5].select("td")[1].text.strip(),
            "avg_headshots": detail_tag.select("tr")[6].select("td")[1].text.strip(),
            "map_play": detail_tag.select("tr")[7].select("td")[1].text.strip(),
        }
        error_tag = {
            "mistake_shout": error_tag.select("tr")[0].select("td")[1].text.strip(),
            "kill_friend": error_tag.select("tr")[1].select("td")[1].text.strip(),
            "down_friend": error_tag.select("tr")[2].select("td")[1].text.strip(),
            "abandon_friend": error_tag.select("tr")[3].select("td")[1].text.strip(),
            "put_into": error_tag.select("tr")[4].select("td")[1].text.strip(),
            "agitate_witch": error_tag.select("tr")[5].select("td")[1].text.strip(),
        }
        inf_avg_dict = {
            "avg_smoker": inf_avg_tag.select("tr")[0].select("td")[1].text.strip(),
            "avg_boomer": inf_avg_tag.select("tr")[1].select("td")[1].text.strip(),
            "avg_hunter": inf_avg_tag.select("tr")[2].select("td")[1].text.strip(),
            "avg_charger": inf_avg_tag.select("tr")[3].select("td")[1].text.strip(),
            "avg_spitter": inf_avg_tag.select("tr")[4].select("td")[1].text.strip(),
            "avg_jockey": inf_avg_tag.select("tr")[5].select("td")[1].text.strip(),
            "avg_tank": inf_avg_tag.select("tr")[6].select("td")[1].text.strip(),
        }
        sur_dict = {
            "map_clear": sur_tag.select("tr")[0].select("td")[1].text.strip(),
            "prefect_into": sur_tag.select("tr")[1].select("td")[1].text.strip(),
            "get_oil": sur_tag.select("tr")[2].select("td")[1].text.strip(),
            "ammo_arrange": sur_tag.select("tr")[3].select("td")[1].text.strip(),
            "adrenaline_give": sur_tag.select("tr")[4].select("td")[1].text.strip(),
            "pills_give": sur_tag.select("tr")[5].select("td")[1].text.strip(),
            "first_aid_give": sur_tag.select("tr")[6].select("td")[1].text.strip(),
            "friend_up": sur_tag.select("tr")[7].select("td")[1].text.strip(),
            "diss_friend": sur_tag.select("tr")[8].select("td")[1].text.strip(),
            "save_friend": sur_tag.select("tr")[9].select("td")[1].text.strip(),
            "protect_friend": sur_tag.select("tr")[10].select("td")[1].text.strip(),
            "pro_from_smoker": sur_tag.select("tr")[11].select("td")[1].text.strip(),
            "pro_from_hunter": sur_tag.select("tr")[12].select("td")[1].text.strip(),
            "pro_from_charger": sur_tag.select("tr")[13].select("td")[1].text.strip(),
            "pro_from_jockey": sur_tag.select("tr")[14].select("td")[1].text.strip(),
            "melee_charge": sur_tag.select("tr")[15].select("td")[1].text.strip(),
            "tank_kill": sur_tag.select("tr")[16].select("td")[1].text.strip(),
            "witch_instantly_kill": sur_tag.select("tr")[17]
            .select("td")[1]
            .text.strip(),
        }
        inf_dict = {
            "sur_ace": inf_tag.select("tr")[0].select("td")[1].text.strip(),
            "sur_down": inf_tag.select("tr")[1].select("td")[1].text.strip(),
            "boommer_hit": inf_tag.select("tr")[2].select("td")[1].text.strip(),
            "hunter_prefect": inf_tag.select("tr")[3].select("td")[1].text.strip(),
            "hunter_success": inf_tag.select("tr")[4].select("td")[1].text.strip(),
            "tank_damage": inf_tag.select("tr")[5].select("td")[1].text.strip(),
            "charger_multiple": inf_tag.select("tr")[6].select("td")[1].text.strip(),
        }
        info_dict = cast(AnnePlayerInfo, info_dict)
        detail_dict = cast(AnnePlayerDetail, detail_tag)
        error_dict = cast(AnnePlayerError, error_tag)
        inf_avg_dict = cast(AnnePlayerInfAvg, inf_avg_dict)
        sur_dict = cast(AnnePlayerSur, sur_dict)
        inf_dict = cast(AnnePlayerInf, inf_dict)

        out_dict = {
            "kill_msg": kill_tag.text if kill_tag is not None else "",
            "info": info_dict,
            "detail": detail_dict,
            "inf_avg": inf_avg_dict,
            "sur": sur_dict,
            "inf": inf_dict,
            "error": error_dict,
        }

        return cast(AnnePlayer2, out_dict)


L4API = L4D2Api()
