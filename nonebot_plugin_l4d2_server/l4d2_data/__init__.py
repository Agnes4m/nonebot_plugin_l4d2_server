from ..config import (
    DATASQLITE,
    table_data,
    L4d2_players_tag,
    L4d2_server_tag,
    L4d2_INTEGER,
    L4d2_TEXT,
    L4d2_BOOLEAN
    )
import sqlite3


tables_columns = {
    table_data[0]:L4d2_players_tag,
    L4d2_server_tag[0]:L4d2_server_tag
}



class L4D2DataSqlite:
    def __init__(self):
        """连接数据库"""
        self.datasqlite_path = DATASQLITE
        self.datasqlite_path.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.datasqlite_path / 'L4D2.db')       
        c = self.conn.cursor()
        # self.
    
    
    def _create_db(self) -> None:
        """创建数据库"""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE L4d2_players 
                  (qq      INTEGER PRIMARY KEY, 
                  nickname TEXT, 
                  STEAMID  TEXT
                  )''')
        c.execute('''CREATE TABLE L4D2_server 
                  (group   INTEGER PRIMARY KEY, 
                  number   INTEGER, 
                  host     TEXT, 
                  port     INTEGER, 
                  rcon     TEXT, 
                  path     TEXT,
                  use      BOOLEAN
                  )''')
        self.conn.commit()
    
        
    def _check_tables_exist(self) -> None:
        """
        检查表是否存在
        tables_columns = {
        'L4d2_players': ['qq', 'nickname', 'steamid'],
        'L4D2_server': ['group', 'number', 'host', 'port', 'rcon', 'path', 'use']
        }
        """  
        c = self.conn.cursor()
        for table in table_data:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if c.fetchone() is None:
                if table == "L4d2_players":
                    c.execute(f"CREATE TABLE {table} ({', '.join(L4d2_players_tag)})")
                elif table == "L4D2_server":
                    c.execute(f"CREATE TABLE {table} ({', '.join(L4d2_server_tag)})")
                self.conn.commit()
        
        
    def _check_data_validity(self) -> None:
        """
        检查数据库数据的合法性
        如果新建列，则旧数据默认填充NULL或者False
        """
        c = self.conn.cursor()
        for table in table_data:
            columns = tables_columns[table]
        for column in columns:
            if column in L4d2_INTEGER:
                c.execute(f"UPDATE {table} SET {column} = NULL WHERE typeof({column}) != 'integer'")
            elif column in L4d2_TEXT:
                c.execute(f"UPDATE {table} SET {column} = NULL WHERE typeof({column}) != 'text'")
            elif column in L4d2_BOOLEAN:
                c.execute(f"UPDATE {table} SET {column} = 'False' WHERE typeof({column}) != 'boolean'")
        self.conn.commit()