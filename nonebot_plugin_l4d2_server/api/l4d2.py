"""L4D2 external API client: A2S queries, SourceBans scraping, Workshop lookup.

Replaces the legacy ``shared/utils/api/request.py``. The dead
``config.json`` override path (which always read an empty ``{}``) has been
removed; the ``url`` argument is used directly.

A2S 性能要点：

- 单批并发上限 ``config.l4_a2s_concurrency``（默认 8），通过 ``asyncio.Semaphore``
  在 ``_a2s_one`` 入口统一收敛。
- 单服结果按 ``(host, port)`` 缓存 ``config.l4_a2s_cache_ttl`` 秒（默认 15），
  避免群里短时间内重复 /云 触发 N 次 UDP；缓存命中时 ``deepcopy`` 返回防止
  下游 mutate 污染条目。
- ainfo / aplayers 超时统一从 ``config.l4_a2s_timeout`` 取，不再硬编码 3 秒。
- ``_empty_source_info`` 改为模块级常量 + deepcopy，每次返回独立对象。
- 仅在 ainfo 抛异常时跳过 aplayers；``player_count == 0`` 不跳过——
  按用户澄清，玩家数与服务器是否开服无关联。
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast

import a2s
from bs4 import BeautifulSoup, Tag
from httpx import AsyncClient
from nonebot.log import logger

from ..config import config
from ..http_helpers import split_maohao
from .models import (
    AnnePlayer2,
    AnnePlayerDetail,
    AnnePlayerInf,
    AnnePlayerInfAvg,
    AnnePlayerInfo,
    AnnePlayerSur,
    AnneSearch,
    SourceBansInfo,
    WorksopInfo,
)
from .sources import AnnePlayerApi, AnneSearchApi, WorkshopApi, anne_ban

# 空 SourceInfo 单例，每次通过 deepcopy 返回独立实例。
_EMPTY_SOURCE_INFO: a2s.SourceInfo = a2s.SourceInfo(
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


def _empty_source_info() -> a2s.SourceInfo:
    return deepcopy(_EMPTY_SOURCE_INFO)


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

    # 每隔这么多秒顺手扫一次过期缓存条目；不需要新线程，挂在批入口即可。
    _CACHE_SWEEP_INTERVAL = 60

    def __init__(self) -> None:
        # concurrency=0 → 不限并发（旧版行为，所有服一次性 asyncio.gather）。
        # 只有显式给 >0 时才走 Semaphore，避免无意义的 await。
        n = int(config.l4_a2s_concurrency)
        self._sem: asyncio.Semaphore | None = asyncio.Semaphore(n) if n > 0 else None
        self._timeout = float(config.l4_a2s_timeout)
        self._ttl = int(config.l4_a2s_cache_ttl)
        # key=(host, port) -> (expire_at_monotonic, (server, players))
        self._cache: dict[
            tuple[str, int],
            tuple[float, tuple[a2s.SourceInfo, list[a2s.Player]]],
        ] = {}
        self._last_sweep = time.monotonic()

    def _cache_key(self, ip: Tuple[str, int]) -> tuple[str, int]:
        return (str(ip[0]), int(ip[1]))

    def _cache_get(
        self,
        key: tuple[str, int],
    ) -> Optional[tuple[a2s.SourceInfo, list[a2s.Player]]]:
        item = self._cache.get(key)
        if item is None:
            return None
        expire_at, value = item
        if expire_at < time.monotonic():
            self._cache.pop(key, None)
            return None
        return value

    def _cache_put(
        self,
        key: tuple[str, int],
        value: tuple[a2s.SourceInfo, list[a2s.Player]],
    ) -> None:
        if self._ttl <= 0:
            return
        self._cache[key] = (time.monotonic() + self._ttl, value)

    def _sweep_cache_if_needed(self) -> None:
        now = time.monotonic()
        if now - self._last_sweep < self._CACHE_SWEEP_INTERVAL:
            return
        self._last_sweep = now
        expired = [k for k, (exp, _) in self._cache.items() if exp < now]
        for k in expired:
            self._cache.pop(k, None)

    # ---------- A2S ----------

    async def a2s_info_single(
        self,
        ip: Tuple[str, int],
    ) -> a2s.SourceInfo[str]:
        """Query a single server; fall back to empty SourceInfo on error."""
        try:
            return await a2s.ainfo(ip, timeout=self._timeout, encoding="utf8")
        except Exception as exc:
            logger.debug(f"A2S 单服查询失败 {ip}: {exc}")
            return _empty_source_info()

    async def a2s_info_batch(
        self,
        ip_list: List[Tuple[str, int]],
        want_players: bool = True,
    ) -> List[Tuple[a2s.SourceInfo[str], List[a2s.Player]]]:
        """Query multiple servers concurrently. Order is stable by steam_id."""
        if not ip_list:
            return []

        self._sweep_cache_if_needed()

        tasks = [
            asyncio.create_task(self._a2s_one(ip, idx, want_players))
            for idx, ip in enumerate(ip_list)
        ]
        try:
            results = await asyncio.gather(*tasks)
        except Exception as exc:
            logger.error(f"批量 A2S 查询失败: {exc}")
            results = [(_empty_source_info(), []) for _ in ip_list]

        return sorted(
            results,
            key=lambda pair: (
                getattr(pair[0], "steam_id", float("inf")) is None,
                getattr(pair[0], "steam_id", float("inf")),
            ),
        )

    async def a2s_info_batch_ordered(
        self,
        ip_list: List[Tuple[str, int]],
        want_players: bool = True,
    ) -> List[Tuple[str, int, a2s.SourceInfo, List[a2s.Player]]]:
        """并发查询多服，返回 ``[(host, port, info, players), ...]``，**保持输入顺序**。

        与 ``a2s_info_batch`` 不同：本方法不按 steam_id 排序，便于上层按
        输入 IP 直接对齐结果（收藏巡检等场景）。底层仍复用 ``_a2s_one`` 的
        信号量 / 缓存 / deepcopy。
        """
        if not ip_list:
            return []

        self._sweep_cache_if_needed()
        results = await asyncio.gather(
            *[
                asyncio.create_task(self._a2s_one(ip, idx, want_players))
                for idx, ip in enumerate(ip_list)
            ],
        )
        return [
            (ip_list[i][0], ip_list[i][1], info, players)
            for i, (info, players) in enumerate(results)
        ]

    async def _a2s_one(
        self,
        ip: Tuple[str, int],
        index: int,
        want_players: bool,
    ) -> Tuple[a2s.SourceInfo, List[a2s.Player]]:
        key = self._cache_key(ip)

        # 缓存命中：deepcopy 防止下游 mutate 污染条目。
        if self._ttl > 0:
            cached = self._cache_get(key)
            if cached is not None:
                server, players = deepcopy(cached)
                server.steam_id = index  # type: ignore[attr-defined]
                return server, (players if want_players else [])

        # 并发 = 0（不限）时直接走裸 await，不引入 Semaphore 的额外等待开销。
        ainfo_cm: contextlib.AbstractAsyncContextManager[Any]
        if self._sem is not None:
            ainfo_cm = self._sem
        else:
            ainfo_cm = contextlib.AsyncExitStack()

        async with ainfo_cm:
            try:
                server = await a2s.ainfo(
                    ip,
                    timeout=self._timeout,
                    encoding="utf8",
                )
                if server is not None:
                    server.steam_id = index  # type: ignore[attr-defined]
                else:
                    server = _empty_source_info()
                    server.steam_id = index  # type: ignore[attr-defined]
            except Exception as exc:
                logger.debug(f"A2S 单服超时/失败 {ip}: {exc}")
                server = _empty_source_info()
                server.steam_id = index  # type: ignore[attr-defined]
                want_players = False

            players: List[a2s.Player] = []
            if want_players:
                with contextlib.suppress(Exception):
                    players = await a2s.aplayers(
                        ip,
                        timeout=self._timeout,
                        encoding="utf8",
                    )

        self._cache_put(key, (server, players))
        # 缓存存入的是 ``server`` 本身；返回前 deepcopy 一份防下游 mutate 直接污染缓存。
        return deepcopy(server), players

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
        _tag: str = "云",
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
                key: trs[i].select("td")[1].text.strip() for i, key in enumerate(keys)
            }

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
