"""L4D2 external API client: A2S queries, SourceBans scraping, Workshop lookup.

Replaces the legacy ``shared/utils/api/request.py``. The dead
``config.json`` override path (which always read an empty ``{}``) has been
removed; the ``url`` argument is used directly.
"""

from __future__ import annotations

import asyncio
import contextlib
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast

import a2s
import httpx
from bs4 import BeautifulSoup, Tag
from httpx import AsyncClient
from nonebot.log import logger

from http_helpers import split_maohao
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
from .sources import AnneSearchApi, AnnePlayerApi, WorkshopApi, anne_ban


class L4D2Api:
    """All HTTP / A2S calls in one place."""

    ssl_verify: bool = False

    _HEADER: Dict[str, str] = {  # noqa: RUF012
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
        ),
        "Content-Type": "application/x-www-form-urlencoded",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    }

    # ---------- A2S ----------

    @staticmethod
    def _empty_source_info() -> a2s.SourceInfo:
        return a2s.SourceInfo(
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

    async def a2s_info_single(
        self, ip: Tuple[str, int]
    ) -> a2s.SourceInfo[str]:
        """Query a single server; fall back to empty SourceInfo on error."""
        try:
            server = await a2s.ainfo(ip, timeout=3, encoding="utf8")
            return server
        except Exception:
            return self._empty_source_info()

    async def a2s_info_batch(
        self,
        ip_list: List[Tuple[str, int]],
        want_players: bool = True,
    ) -> List[Tuple[a2s.SourceInfo[str], List[a2s.Player]]]:
        """Query multiple servers in parallel. Order is stable by steam_id."""
        if not ip_list:
            return []

        tasks = [
            asyncio.create_task(self._a2s_one(ip, idx, want_players))
            for idx, ip in enumerate(ip_list)
        ]
        try:
            results = await asyncio.gather(*tasks)
        except Exception as exc:
            logger.error(f"批量 A2S 查询失败: {exc}")
            results = [(self._empty_source_info(), []) for _ in ip_list]

        return sorted(
            results,
            key=lambda pair: (
                    getattr(pair[0], "steam_id", float("inf")) is None,
                    getattr(pair[0], "steam_id", float("inf")),
                ),
            )

    async def _a2s_one(
        self,
        ip: Tuple[str, int],
        index: int,
        want_players: bool,
    ) -> Tuple[a2s.SourceInfo, List[a2s.Player]]:
        server: Union[a2s.SourceInfo, a2s.GoldSrcInfo]
        try:
            server = await a2s.ainfo(ip, timeout=3, encoding="utf8")
            if server is not None:
                server.steam_id = index  # type: ignore[attr-defined]
        except Exception:
            server = self._empty_source_info()
            server.steam_id = index  # type: ignore[attr-defined]
            want_players = False

        players: List[a2s.Player] = []
        if want_players:
            with contextlib.suppress(Exception):
                players = await a2s.aplayers(ip, timeout=3, encoding="utf8")
        return server, players

    # ---------- HTTP ----------

    async def _request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any] | list] = None,
        data: Optional[Dict[str, Any]] = None,
        expect_json: bool = True,
    ) -> Union[Dict[str, Any], BeautifulSoup]:  # type: ignore[return-value]
        headers = deepcopy(self._HEADER)
        if method == "GET" and json_body is not None:
            method = "POST"

        async with AsyncClient(verify=self.ssl_verify) as client:
            resp = await client.request(
                method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                data=data,
                timeout=300,
            )

        if not expect_json:
            return BeautifulSoup(resp.content, "lxml")

        try:
            raw = resp.json()
        except Exception:
            text = resp.text
            try:
                import ujson as json  # type: ignore[import-not-found]
                raw = json.loads(text)
            except Exception:
                raw = {"result": {"error_code": -999, "data": text}}

        try:
            if not raw.get("result"):
                return raw
        except Exception:
            return raw

        if (
            "result" in raw
            and isinstance(raw["result"], dict)
            and "error_code" in raw["result"]
            and raw.get("code") != 200
        ):
            return raw["result"]["error_code"]
        return raw

    # ---------- SourceBans ----------

    async def get_sourceban(
        self,
        tag: str = "云",
        url: str = anne_ban,
    ) -> List[SourceBansInfo]:
        """Scrape a SourceBans++ page and return server info objects."""
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        resp = await self._request(url=url, expect_json=False)
        if not isinstance(resp, BeautifulSoup):
            return []

        servers: List[SourceBansInfo] = []
        tbody = resp.select_one("tbody")
        if tbody is None:
            return []

        for index, tr in enumerate(tbody.select("tr")):
            td_tags = tr.find_all("td")
            if len(td_tags) < 5:
                continue
            host, port = split_maohao(td_tags[4].text)
            servers.append(SourceBansInfo(index=index, host=host, port=port))
        return servers

    # ---------- Anne (电信服) ----------

    async def get_anne_steamid(self, name: str) -> Optional[List[AnneSearch]]:
        """Search Anne player database by nickname."""
        resp = await self._request(
            url=AnneSearchApi,
            data={"search": name},
            method="POST",
            expect_json=False,
        )
        if not isinstance(resp, BeautifulSoup):
            return None

        tbody = resp.select_one("tbody")
        if tbody is None:
            return None

        results: List[AnneSearch] = []
        for tr in tbody.select("tr"):
            onclick = tr.get("onclick")
            if onclick is None or isinstance(onclick, list):
                continue
            steamid = onclick.split("steamid=")[1].replace("'", "")
            td_tags = tr.select("td")
            results.append(
                {
                    "steamid": steamid,
                    "rank": td_tags[0].text.strip(),
                    "name": td_tags[1].text.strip(),
                    "score": td_tags[2].text.strip(),
                    "play_time": td_tags[3].text.strip(),
                    "last_time": td_tags,
                },
            )
        logger.debug(results)
        return results

    async def get_anne_playerdetail(self, steamid: str) -> Optional[AnnePlayer2]:
        """Fetch Anne player details by steamid."""
        resp = await self._request(
            url=AnnePlayerApi,
            method="GET",
            params={"steamid": steamid},
            expect_json=False,
        )
        if not isinstance(resp, BeautifulSoup):
            return None

        tbody = resp.find(
            "div",
            class_="content text-center text-md-left",
            style="background-color: #f2f2f2;",
        )
        if tbody is None:
            return None

        if not isinstance(tbody, Tag):
            return None

        kill_tag = tbody.find(
            "div",
            class_="card-body worldmap d-flex flex-column justify-content-center text-center",
        )

        tbody_tags = tbody.find_all(
            "table",
            class_="table content-table-noborder text-left",
        )
        if len(tbody_tags) < 6:
            return None

        def get_table_dict(table, keys):
            trs = table.select("tr")
            return {
                key: trs[i].select("td")[1].text.strip()
                for i, key in enumerate(keys)
            }

        info_keys = ["name", "avatar", "steamid", "playtime", "lasttime"]
        detail_keys = [
            "rank", "source", "avg_source", "kills", "kills_people",
            "headshots", "avg_headshots", "map_play",
        ]
        error_keys = [
            "mistake_shout", "kill_friend", "down_friend", "abandon_friend",
            "put_into", "agitate_witch",
        ]
        inf_avg_keys = [
            "avg_smoker", "avg_boomer", "avg_hunter", "avg_charger",
            "avg_spitter", "avg_jockey", "avg_tank",
        ]
        sur_keys = [
            "map_clear", "prefect_into", "get_oil", "ammo_arrange",
            "adrenaline_give", "pills_give", "first_aid_give", "friend_up",
            "diss_friend", "save_friend", "protect_friend",
            "pro_from_smoker", "pro_from_hunter", "pro_from_charger",
            "pro_from_jockey", "melee_charge", "tank_kill",
            "witch_instantly_kill",
        ]
        inf_keys = [
            "sur_ace", "sur_down", "boommer_hit", "hunter_prefect",
            "hunter_success", "tank_damage", "charger_multiple",
        ]

        info_dict = get_table_dict(tbody_tags[0], info_keys)
        detail_dict = get_table_dict(tbody_tags[1], detail_keys)
        error_dict = get_table_dict(tbody_tags[2], error_keys)
        inf_avg_dict = get_table_dict(tbody_tags[3], inf_avg_keys)
        sur_dict = get_table_dict(tbody_tags[4], sur_keys)
        inf_dict = get_table_dict(tbody_tags[5], inf_keys)

        return cast(
            AnnePlayer2,
            {
                "kill_msg": kill_tag.text.strip() if kill_tag else "",
                "info": cast(AnnePlayerInfo, info_dict),
                "detail": cast(AnnePlayerDetail, detail_dict),
                "inf_avg": cast(AnnePlayerInfAvg, inf_avg_dict),
                "sur": cast(AnnePlayerSur, sur_dict),
                "inf": cast(AnnePlayerInf, inf_dict),
                "error": error_dict,
            },
        )

    # ---------- Steam Workshop ----------

    async def workshops(self, workshop_id: str) -> WorksopInfo:
        """Fetch Workshop item details by id."""
        resp = await self._request(
            url=WorkshopApi,
            method="POST",
            json_body=[int(workshop_id)],
            expect_json=True,
        )
        if not isinstance(resp, dict):
            raise TypeError("请求创意工坊失败")

        if (
            "result" in resp
            and isinstance(resp["result"], list)
            and len(resp["result"]) > 0
        ):
            return cast(WorksopInfo, resp["result"][0])
        if len(resp) > 0:
            return cast(WorksopInfo, resp)
        raise ValueError("没有找到创意工坊内容")


# Module-level singleton.
L4API = L4D2Api()