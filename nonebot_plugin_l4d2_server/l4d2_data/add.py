from ..config import DATASQLITE
import sqlite3
from typing import Union

class L4D2Change:
    """数据库角色信息处理"""
    def __init__(self, DATASQLITE):
        self.DATASQLITE = DATASQLITE
        self.conn = sqlite3.connect(self.DATASQLITE/ 'L4D2.db')
        self.c = self.conn.cursor()
            
    def _add_player_nickname(self, qq, nickname):
        """绑定昵称"""
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO players (qq, nickname, steamid) VALUES (?,?,NULL)", (qq, nickname))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Player with qq: {qq} already exists.")
              
    def _add_player_steamid(self, qq, steamid):
        """绑定steamid"""
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO players (qq, nickname, steamid) VALUES (?,NULL,?)", (qq, steamid))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Player with qq: {qq} already exists.")
        
    def _delete_player(self, qq):
        """解除绑定"""
        self.c.execute(f"DELETE FROM players WHERE qq = {qq}")
        self.conn.commit()
        print("Player Delete Success")
        
    def _query_player(self, qq):
        """查询用户是否存在"""
        self.c.execute(f"SELECT * FROM players WHERE qq = {qq}")
        return self.c.fetchone()
    
    def search_data(self, data:tuple) -> Union[tuple,None]:
        """
        输入元组查询，优先qq其次steamid最后nickname，不需要值可以为None
        输出为元组，如果为空输出None
        data = (qq , nickname , steamid )
        
        """
        qq, nickname, steamid = data
        c = self.conn.cursor()
        if qq:
            c.execute("SELECT * FROM players WHERE qq=?", (qq,))
            result = c.fetchone()
            if result:
                return result
        if steamid:
            c.execute("SELECT * FROM players WHERE steamid=?", (steamid,))
            result = c.fetchone()
            if result:
                return result
        if nickname:
            c.execute("SELECT * FROM players WHERE nickname=?", (nickname,))
            result = c.fetchone()
            if result:
                return result
        return None
    
    def _query_all_player(self):
        """清空绑定"""
        self.c.execute("SELECT * FROM players")
        return self.c.fetchall()
    
    def _close(self):
        self.conn.close()
