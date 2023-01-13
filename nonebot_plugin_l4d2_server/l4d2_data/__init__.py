from ..config import DATASQLITE
import sqlite3


class L4D2DataSqlite:
    def __init__(self):
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
        c.execute('''CREATE TABLE server 
                  (group   INTEGER PRIMARY KEY, 
                  number   INTEGER, 
                  host     TEXT, 
                  port     INTEGER, 
                  rcon     TEXT, 
                  path     TEXT
                  )''')
        self.conn.commit()
    
    def _check_data(self):
        """检查数据库完整"""
        c = self.conn.cursor()
        # Check if the players table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
        if c.fetchone() is None:
            # Create the players table if it doesn't exist
            c.execute('''CREATE TABLE players
                        (qq INTEGER PRIMARY KEY,
                        nickname TEXT,
                        steamid INTEGER)''')
            self.conn.commit()
            print("players table created.")
        else:
            # Check if the players table has the correct columns
            c.execute("PRAGMA table_info(players)")
            columns = [col[1] for col in c.fetchall()]
            if 'qq' not in columns:
                c.execute("ALTER TABLE players ADD COLUMN qq INTEGER PRIMARY KEY")
                self.conn.commit()
                print("qq column added to players table.")
            if 'nickname' not in columns:
                c.execute("ALTER TABLE players ADD COLUMN nickname TEXT")
                self.conn.commit()
                print("nickname column added to players table.")
            if 'steamid' not in columns:
                c.execute("ALTER TABLE players ADD COLUMN steamid INTEGER")
                self.conn.commit()
                print("steamid column added to players table.")



