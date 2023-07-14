# -*- coding: utf-8 -*-
from pydantic import BaseModel


class GROUP_MSG(BaseModel):
    tag:str
    online_server:int
    empty_server:int
    full_server:int
    max_server:int
    
    online_player:int
    max_player:int
    
    def __str__(self) -> str:
        return f"""组:{self.tag}
    在线服务器:{self.online_server}/{self.max_server}
    空服务器:{self.empty_server}/{self.max_server}
    在线玩家数量:{self.online_player}/{self.max_player}"""
    
