import json as js
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Union

import a2s
from httpx import AsyncClient
from lxml import etree

from ..utils import split_maohao
from .api import anne_ban
from .models import SourceBansInfo


class L4D2Api:
    ssl_verify = False
    _HEADER: Dict[str, str] = {  # noqa: RUF012
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko)"
        "Chrome/126.0.0.0"
        "Safari/537.36 Edg/126.0.0.0",
    }

    async def a2s_info(
        self,
        host: str,
        port: int,
    ) -> a2s.SourceInfo:
        msg: a2s.SourceInfo = await a2s.ainfo((host, port))
        return msg

    async def a2s_players(
        self,
        host: str,
        port: int,
    ) -> List[a2s.Player]:
        msg: List[a2s.Player] = await a2s.aplayers((host, port))
        return msg

    async def _server_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        header: Dict[str, str] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_json: bool = True,
    ) -> Union[Dict, int]:
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
            return etree.HTML(html_content)

    async def get_sourceban(self, name: str, url: str = anne_ban):
        tree = await self._server_request(
            url=url,
            is_json=False,
        )  # type: ignore
        name = name
        # 检查响应状态码

        target_element = tree.xpath(
            "/html/body/main/div[3]/div[5]/div/div/table/tbody/tr",
        )
        server_list = []
        # for tr in target_element:
        for tr in target_element:
            if tr.get("class") != "collapse":
                continue
            index = 0
            for td in tr.xpath("./td"):
                if td.get("id") is not None or td.text == "\n":
                    continue
                index += 1
                host, port = split_maohao(td.text)
                server_list.append(SourceBansInfo(index=index, host=host, port=port))

        # 通过一次请求，确定服务器的序号
        return server_list


L4API = L4D2Api()
