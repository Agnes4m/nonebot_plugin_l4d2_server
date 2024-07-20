from typing import List, TypedDict

import a2s


class PluginSV(TypedDict):
    name: str
    desc: str
    eg: str
    need_ck: bool
    need_sk: bool
    need_admin: bool


class PluginHelp(TypedDict):
    desc: str
    data: List[PluginSV]

